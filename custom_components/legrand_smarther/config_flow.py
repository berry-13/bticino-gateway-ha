"""Config flow for Legrand Smarther integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers import config_validation as cv

from .api import SmartherAPI, SmartherAPIError
from .const import (
    CONF_ENABLE_EXTRA_SENSORS,
    CONF_MODULES,
    CONF_TEMPERATURE_STEP,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_CHRONOTHERMOSTAT,
    DOMAIN,
    INTEGRATION_NAME,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    TEMP_STEP_HALF,
    TEMP_STEP_TENTH,
)

_LOGGER = logging.getLogger(__name__)


class LegrandSmartherFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle a config flow for Legrand Smarther."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize the config flow."""
        super().__init__()
        self._oauth_data: Optional[Dict[str, Any]] = None
        self._plants: list = []
        self._modules: list = []

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Check if we have application credentials configured
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            self.hass, DOMAIN
        )

        if not implementations:
            return self.async_show_form(
                step_id="user",
                errors={"base": "no_application_credentials"},
                description_placeholders={
                    "more_info_url": "https://github.com/berry-13/bticino-gateway-ha#setup"
                },
            )

        # Start OAuth2 flow - AbstractOAuth2FlowHandler will handle this
        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: Dict[str, Any]) -> FlowResult:
        """Create an entry after OAuth2 authorization."""
        self._oauth_data = data

        try:
            # Test the API connection and fetch plants
            oauth_session = config_entry_oauth2_flow.OAuth2Session(
                self.hass, None, self.flow_implementation, data["token"]
            )
            api = SmartherAPI(self.hass, oauth_session)

            self._plants = await api.list_plants()

            if not self._plants:
                return self.async_abort(reason="no_plants")

            # Fetch modules for all plants
            self._modules = []
            for plant in self._plants:
                try:
                    topology = await api.get_plant_topology(plant["id"])
                    modules = topology.get("modules", [])

                    for module in modules:
                        if module.get("device") == DEVICE_TYPE_CHRONOTHERMOSTAT:
                            self._modules.append(
                                {
                                    "plant_id": plant["id"],
                                    "plant_name": plant["name"],
                                    "module_id": module["id"],
                                    "module_name": module["name"],
                                    "device_type": module["device"],
                                }
                            )
                except SmartherAPIError as err:
                    _LOGGER.warning(
                        "Error fetching topology for plant %s: %s", plant["id"], err
                    )
                    continue

            if not self._modules:
                return self.async_abort(reason="no_modules")

            return await self.async_step_select_modules()

        except SmartherAPIError as err:
            _LOGGER.error("Error testing API connection: %s", err)
            return self.async_abort(reason="auth_error")
        except Exception as err:
            _LOGGER.exception("Unexpected error during OAuth flow: %s", err)
            return self.async_abort(reason="unknown")

    async def async_step_select_modules(self, user_input=None):
        """Allow user to select which modules to add."""
        if user_input is not None:
            selected_modules = user_input[CONF_MODULES]

            if not selected_modules:
                return self.async_show_form(
                    step_id="select_modules",
                    data_schema=self._get_modules_schema(),
                    errors={"base": "no_modules_selected"},
                )

            # Create config entries for selected modules
            entries_created = 0
            for module_id in selected_modules:
                module = next(
                    (m for m in self._modules if m["module_id"] == module_id), None
                )
                if module:
                    # Check if this module is already configured
                    existing_entry = await self.async_set_unique_id(
                        f"{DOMAIN}_{module_id}"
                    )
                    if existing_entry:
                        self.hass.config_entries.async_update_entry(
                            existing_entry, data={**self._oauth_data, **module}
                        )
                    else:
                        entry_data = {**self._oauth_data, **module}
                        await self.async_create_entry(
                            title=f"{module['plant_name']} - {module['module_name']}",
                            data=entry_data,
                        )
                        entries_created += 1

            if entries_created == 0:
                return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=INTEGRATION_NAME,
                data=self._oauth_data,
            )

        return self.async_show_form(
            step_id="select_modules",
            data_schema=self._get_modules_schema(),
        )

    def _get_modules_schema(self):
        """Get schema for module selection."""
        options = {}
        for module in self._modules:
            key = module["module_id"]
            label = f"{module['plant_name']} - {module['module_name']}"
            options[key] = label

        return vol.Schema(
            {
                vol.Required(CONF_MODULES): vol.All(
                    cv.multi_select(options), vol.Length(min=1)
                )
            }
        )

    async def async_step_reauth(self, entry_data: Dict[str, Any]) -> FlowResult:
        """Handle reauth flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Confirm reauth flow."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")

        # Use the parent class implementation for reauth
        return await self.async_step_pick_implementation()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Legrand Smarther."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=options.get("scan_interval", DEFAULT_SCAN_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_TEMPERATURE_STEP,
                        default=options.get(CONF_TEMPERATURE_STEP, TEMP_STEP_HALF),
                    ): vol.In({TEMP_STEP_HALF: "0.5°C", TEMP_STEP_TENTH: "0.1°C"}),
                    vol.Optional(
                        CONF_ENABLE_EXTRA_SENSORS,
                        default=options.get(CONF_ENABLE_EXTRA_SENSORS, True),
                    ): bool,
                }
            ),
        )
