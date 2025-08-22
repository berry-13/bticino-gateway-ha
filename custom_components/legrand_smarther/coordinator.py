"""DataUpdateCoordinator for Legrand Smarther."""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SmartherAPI,
    SmartherAPIError,
    SmartherAuthError,
    SmartherNotFoundError,
    SmartherServerError,
    SmartherTimeoutError,
)
from .const import (
    ATTR_API_ERROR_CODE,
    ATTR_API_ERROR_MESSAGE,
    ATTR_LAST_UPDATE,
    ATTR_MODULE_ID,
    ATTR_PLANT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SmartherDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Smarther API."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth_session: OAuth2Session,
        plant_id: str,
        module_id: str,
        module_name: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ):
        """Initialize."""
        self.api = SmartherAPI(hass, oauth_session)
        self.oauth_session = oauth_session
        self.plant_id = plant_id
        self.module_id = module_id
        self.module_name = module_name
        self._available = True
        self._last_update_success = True
        self._error_info: Optional[Dict[str, Any]] = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{module_name}",
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def available(self) -> bool:
        """Return if the coordinator is available."""
        return self._available

    @property
    def error_info(self) -> Optional[Dict[str, Any]]:
        """Return error information if any."""
        return self._error_info

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            # Fetch both status and measures data
            status_task = self.api.get_chronothermostat_status(
                self.plant_id, self.module_id
            )
            measures_task = self.api.get_chronothermostat_measures(
                self.plant_id, self.module_id
            )

            status_data, measures_data = await asyncio.gather(
                status_task, measures_task, return_exceptions=True
            )

            # Handle status data errors
            if isinstance(status_data, Exception):
                if isinstance(status_data, SmartherNotFoundError):
                    _LOGGER.warning(
                        "Module %s in plant %s not found, marking as unavailable",
                        self.module_id,
                        self.plant_id,
                    )
                    self._available = False
                    self._error_info = {
                        ATTR_API_ERROR_CODE: status_data.status_code,
                        ATTR_API_ERROR_MESSAGE: str(status_data),
                    }
                    # Return empty data but don't raise exception to avoid marking coordinator as failed
                    return {}
                elif isinstance(status_data, SmartherAuthError):
                    _LOGGER.error(
                        "Authentication error for module %s: %s",
                        self.module_id,
                        status_data,
                    )
                    raise status_data  # This will trigger reauth flow
                else:
                    _LOGGER.error(
                        "Error fetching status for module %s: %s",
                        self.module_id,
                        status_data,
                    )
                    raise UpdateFailed(f"Error fetching status: {status_data}")

            # Handle measures data errors
            if isinstance(measures_data, Exception):
                if isinstance(measures_data, SmartherNotFoundError):
                    _LOGGER.warning(
                        "Measures for module %s not found, using status data only",
                        self.module_id,
                    )
                    measures_data = {}
                elif isinstance(measures_data, SmartherAuthError):
                    _LOGGER.error(
                        "Authentication error for measures %s: %s",
                        self.module_id,
                        measures_data,
                    )
                    raise measures_data  # This will trigger reauth flow
                else:
                    _LOGGER.warning(
                        "Error fetching measures for module %s: %s",
                        self.module_id,
                        measures_data,
                    )
                    measures_data = {}

            # Process the data
            data = {
                "status": status_data,
                "measures": measures_data,
                ATTR_PLANT_ID: self.plant_id,
                ATTR_MODULE_ID: self.module_id,
                ATTR_LAST_UPDATE: self.hass.util.dt.utcnow().isoformat(),
            }

            # Clear error info on successful update
            self._available = True
            self._error_info = None
            self._last_update_success = True

            _LOGGER.debug("Successfully updated data for module %s", self.module_id)
            return data

        except SmartherAuthError:
            # Re-raise auth errors to trigger reauth flow
            _LOGGER.error("Authentication failed for module %s", self.module_id)
            raise

        except (SmartherTimeoutError, SmartherServerError) as err:
            # These errors should be retried by the coordinator
            _LOGGER.warning(
                "Temporary error updating module %s: %s", self.module_id, err
            )
            self._last_update_success = False
            raise UpdateFailed(f"Temporary error: {err}")

        except SmartherAPIError as err:
            # Other API errors
            _LOGGER.error("API error updating module %s: %s", self.module_id, err)
            self._error_info = {
                ATTR_API_ERROR_CODE: err.status_code,
                ATTR_API_ERROR_MESSAGE: str(err),
            }

            # For certain errors, mark as unavailable but don't fail the coordinator
            if err.status_code in (469, 470):
                self._available = False
                return {}

            raise UpdateFailed(f"API error: {err}")

        except Exception as err:
            _LOGGER.exception("Unexpected error updating module %s", self.module_id)
            raise UpdateFailed(f"Unexpected error: {err}")

    async def async_set_target_temperature(self, temperature: float) -> None:
        """Set target temperature."""
        try:
            # Get current status to maintain other settings
            current_data = self.data or {}
            current_status = current_data.get("status", {})

            function = current_status.get("function", "heating")

            await self.api.set_chronothermostat_status(
                self.plant_id,
                self.module_id,
                function=function,
                mode="manual",
                setpoint_value=str(temperature),
                setpoint_unit="C",
            )

            # Request immediate data refresh
            await self.async_request_refresh()

        except SmartherAPIError as err:
            _LOGGER.error(
                "Error setting temperature for module %s: %s", self.module_id, err
            )
            raise err

    async def async_set_hvac_mode(self, mode: str) -> None:
        """Set HVAC mode."""
        try:
            # Get current status to maintain other settings
            current_data = self.data or {}
            current_status = current_data.get("status", {})

            function = current_status.get("function", "heating")
            setpoint = current_status.get("setPoint", {})

            data = {
                "function": function,
                "mode": mode,
            }

            # Include setpoint for manual mode
            if mode == "manual" and setpoint:
                data["setPoint"] = setpoint

            await self.api.set_chronothermostat_status(
                self.plant_id, self.module_id, **data
            )

            # Request immediate data refresh
            await self.async_request_refresh()

        except SmartherAPIError as err:
            _LOGGER.error(
                "Error setting HVAC mode for module %s: %s", self.module_id, err
            )
            raise err

    async def async_set_preset_mode(
        self, preset_mode: str, program_number: Optional[int] = None
    ) -> None:
        """Set preset mode."""
        try:
            # Get current status to maintain other settings
            current_data = self.data or {}
            current_status = current_data.get("status", {})

            function = current_status.get("function", "heating")

            if preset_mode == "automatic" and program_number is not None:
                await self.api.set_chronothermostat_status(
                    self.plant_id,
                    self.module_id,
                    function=function,
                    mode="automatic",
                    program_number=program_number,
                )
            else:
                await self.api.set_chronothermostat_status(
                    self.plant_id, self.module_id, function=function, mode=preset_mode
                )

            # Request immediate data refresh
            await self.async_request_refresh()

        except SmartherAPIError as err:
            _LOGGER.error(
                "Error setting preset mode for module %s: %s", self.module_id, err
            )
            raise err
