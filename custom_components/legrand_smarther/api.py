"""API client for Legrand Smarther v2."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    ERROR_CODES,
    USER_ERROR_MESSAGES,
)

_LOGGER = logging.getLogger(__name__)


class SmartherAPIError(Exception):
    """Base exception for Smarther API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the exception."""
        super().__init__(message)
        self.status_code = status_code


class SmartherAuthError(SmartherAPIError):
    """Authentication error."""


class SmartherConnectionError(SmartherAPIError):
    """Connection error."""


class SmartherTimeoutError(SmartherAPIError):
    """Timeout error."""


class SmartherNotFoundError(SmartherAPIError):
    """Resource not found error."""


class SmartherBadRequestError(SmartherAPIError):
    """Bad request error."""


class SmartherServerError(SmartherAPIError):
    """Server error."""


class SmartherAPI:
    """API client for Legrand Smarther v2."""

    def __init__(self, hass: HomeAssistant, oauth_session: OAuth2Session):
        """Initialize the API client."""
        self.hass = hass
        self.oauth_session = oauth_session
        self.session = async_get_clientsession(hass)
        self._base_url = API_BASE_URL

    async def _request(
        self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request with retry logic."""
        await self.oauth_session.async_ensure_token_valid()

        headers = {
            "Authorization": f"Bearer {self.oauth_session.token['access_token']}",
            "Content-Type": "application/json",
        }

        url = f"{self._base_url}{endpoint}"

        # Exponential backoff for retries on 408 and 500 errors
        max_retries = 4
        base_delay = 1

        for attempt in range(max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
                async with self.session.request(
                    method, url, headers=headers, json=json_data, timeout=timeout
                ) as response:

                    # Handle successful responses
                    if response.status == 200:
                        if response.content_type == "application/json":
                            return await response.json()
                        return {}
                    elif response.status == 201:
                        if response.content_type == "application/json":
                            return await response.json()
                        return {}
                    elif response.status == 204:
                        return {}

                    # Handle error responses
                    error_data = {}
                    if response.content_type == "application/json":
                        try:
                            error_data = await response.json()
                        except Exception:
                            pass

                    error_message = error_data.get(
                        "message",
                        ERROR_CODES.get(response.status, f"HTTP {response.status}"),
                    )
                    user_message = USER_ERROR_MESSAGES.get(
                        response.status, error_message
                    )

                    # Authentication errors - trigger reauth
                    if response.status == 401:
                        raise SmartherAuthError(user_message, response.status)

                    # Not found errors - mark entity unavailable but don't fail completely
                    elif response.status == 404:
                        raise SmartherNotFoundError(user_message, response.status)

                    # Bad request errors - don't retry
                    elif response.status == 400:
                        raise SmartherBadRequestError(user_message, response.status)

                    # Special Legrand errors - don't retry, surface to user
                    elif response.status == 469:
                        raise SmartherAPIError(user_message, response.status)
                    elif response.status == 470:
                        raise SmartherAPIError(user_message, response.status)

                    # Timeout and server errors - retry with backoff
                    elif response.status in (408, 500):
                        if attempt < max_retries:
                            delay = base_delay * (2**attempt)
                            _LOGGER.warning(
                                "API request failed with status %s, retrying in %s seconds (attempt %s/%s)",
                                response.status,
                                delay,
                                attempt + 1,
                                max_retries + 1,
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            if response.status == 408:
                                raise SmartherTimeoutError(
                                    user_message, response.status
                                )
                            else:
                                raise SmartherServerError(user_message, response.status)

                    # Other errors - don't retry
                    else:
                        raise SmartherAPIError(user_message, response.status)

            except asyncio.TimeoutError as err:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    _LOGGER.warning(
                        "API request timeout, retrying in %s seconds (attempt %s/%s)",
                        delay,
                        attempt + 1,
                        max_retries + 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise SmartherTimeoutError("Request timeout") from err

            except aiohttp.ClientError as err:
                if attempt < max_retries and isinstance(
                    err,
                    (aiohttp.ClientConnectionError, aiohttp.ServerDisconnectedError),
                ):
                    delay = base_delay * (2**attempt)
                    _LOGGER.warning(
                        "Connection error, retrying in %s seconds (attempt %s/%s): %s",
                        delay,
                        attempt + 1,
                        max_retries + 1,
                        err,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise SmartherConnectionError(f"Connection error: {err}") from err

    async def list_plants(self) -> List[Dict[str, Any]]:
        """Get list of plants associated with the user."""
        _LOGGER.debug("Fetching plants list")
        response = await self._request("GET", "/plants")
        return response.get("plants", [])

    async def get_plant_topology(self, plant_id: str) -> Dict[str, Any]:
        """Get the complete topology of a plant."""
        _LOGGER.debug("Fetching topology for plant %s", plant_id)
        response = await self._request("GET", f"/plants/{plant_id}/topology")
        return response.get("plant", {})

    async def get_chronothermostat_status(
        self, plant_id: str, module_id: str
    ) -> Dict[str, Any]:
        """Get the complete status of a chronothermostat."""
        _LOGGER.debug("Fetching status for module %s in plant %s", module_id, plant_id)
        endpoint = f"/chronothermostat/thermoregulation/addressLocation/plants/{plant_id}/modules/parameter/id/value/{module_id}"
        response = await self._request("GET", endpoint)
        chronothermostats = response.get("chronothermostats", [])
        return chronothermostats[0] if chronothermostats else {}

    async def get_chronothermostat_measures(
        self, plant_id: str, module_id: str
    ) -> Dict[str, Any]:
        """Get the measured temperature and humidity detected by a chronothermostat."""
        _LOGGER.debug(
            "Fetching measures for module %s in plant %s", module_id, plant_id
        )
        endpoint = f"/chronothermostat/thermoregulation/addressLocation/plants/{plant_id}/modules/parameter/id/value/{module_id}/measures"
        return await self._request("GET", endpoint)

    async def set_chronothermostat_status(
        self,
        plant_id: str,
        module_id: str,
        function: str,
        mode: str,
        setpoint_value: Optional[str] = None,
        setpoint_unit: str = "C",
        program_number: Optional[int] = None,
        activation_time: Optional[str] = None,
    ) -> None:
        """Set the status of a chronothermostat."""
        _LOGGER.debug(
            "Setting status for module %s in plant %s: function=%s, mode=%s, setpoint=%s",
            module_id,
            plant_id,
            function,
            mode,
            setpoint_value,
        )

        endpoint = f"/chronothermostat/thermoregulation/addressLocation/plants/{plant_id}/modules/parameter/id/value/{module_id}"

        data = {
            "function": function,
            "mode": mode,
        }

        if setpoint_value is not None:
            data["setPoint"] = {"value": setpoint_value, "unit": setpoint_unit}

        if program_number is not None:
            data["programs"] = [{"number": program_number}]

        if activation_time is not None:
            data["activationTime"] = activation_time

        await self._request("POST", endpoint, data)

    async def get_chronothermostat_programs(
        self, plant_id: str, module_id: str
    ) -> List[Dict[str, Any]]:
        """Get the list of programs managed by a chronothermostat."""
        _LOGGER.debug(
            "Fetching programs for module %s in plant %s", module_id, plant_id
        )
        endpoint = f"/chronothermostat/thermoregulation/addressLocation/plants/{plant_id}/modules/parameter/id/value/{module_id}/programlist"
        response = await self._request("GET", endpoint)
        chronothermostats = response.get("chronothermostats", [])
        if chronothermostats:
            return chronothermostats[0].get("programs", [])
        return []
