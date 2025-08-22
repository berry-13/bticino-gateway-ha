"""Climate platform for Legrand Smarther."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SmartherAPIError
from .const import (
    ATTR_ACTIVATION_TIME,
    ATTR_DEVICE_TYPE,
    ATTR_LOAD_STATE,
    ATTR_MODULE_ID,
    ATTR_PLANT_ID,
    ATTR_PROGRAM_NUMBER,
    ATTR_PROGRAMS,
    ATTR_TEMPERATURE_FORMAT,
    CONF_TEMPERATURE_STEP,
    DOMAIN,
    LOAD_STATE_ACTIVE,
    TEMP_STEP_HALF,
    THERMOSTAT_FUNCTION_COOLING,
    THERMOSTAT_FUNCTION_HEATING,
    THERMOSTAT_MODE_AUTOMATIC,
    THERMOSTAT_MODE_BOOST,
    THERMOSTAT_MODE_MANUAL,
    THERMOSTAT_MODE_OFF,
    THERMOSTAT_MODE_PROTECTION,
)
from .coordinator import SmartherDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Map Smarther modes to HA HVAC modes
SMARTHER_TO_HVAC_MODE = {
    THERMOSTAT_MODE_OFF: HVACMode.OFF,
    THERMOSTAT_MODE_MANUAL: HVACMode.HEAT,
    THERMOSTAT_MODE_AUTOMATIC: HVACMode.AUTO,
    THERMOSTAT_MODE_BOOST: HVACMode.HEAT,
    THERMOSTAT_MODE_PROTECTION: HVACMode.HEAT,
}

# Map HA HVAC modes to Smarther modes
HVAC_MODE_TO_SMARTHER = {v: k for k, v in SMARTHER_TO_HVAC_MODE.items()}

# Available HVAC modes
HVAC_MODES = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]

# Preset modes
PRESET_MODES = ["automatic", "manual", "boost", "protection"]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Legrand Smarther climate entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = [LegrandSmartherClimate(coordinator, config_entry)]
    async_add_entities(entities)


class LegrandSmartherClimate(CoordinatorEntity, ClimateEntity):
    """Legrand Smarther climate entity."""

    def __init__(
        self,
        coordinator: SmartherDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_unique_id = f"{DOMAIN}_{coordinator.module_id}_climate"
        self._attr_name = f"{coordinator.module_name} Climate"

        # Climate entity features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )

        # Temperature unit
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

        # Temperature step from options
        self._attr_target_temperature_step = config_entry.options.get(
            CONF_TEMPERATURE_STEP, TEMP_STEP_HALF
        )

        # HVAC modes
        self._attr_hvac_modes = HVAC_MODES

        # Preset modes
        self._attr_preset_modes = PRESET_MODES

        # Temperature limits
        self._attr_min_temp = 3.0
        self._attr_max_temp = 40.0

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.module_id)},
            "name": self.coordinator.module_name,
            "manufacturer": "Legrand",
            "model": "Smarther v2",
            "sw_version": "v2.0",
            "via_device": (DOMAIN, self.coordinator.plant_id),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.available and self.coordinator.last_update_success

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        if not self.coordinator.data:
            return None

        status = self.coordinator.data.get("status", {})
        thermometer = status.get("thermometer", {})
        measures = thermometer.get("measures", [])

        if measures:
            # Get the latest temperature reading
            latest_measure = measures[-1]
            try:
                return float(latest_measure.get("value", 0))
            except (ValueError, TypeError):
                return None

        return None

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None

        status = self.coordinator.data.get("status", {})
        setpoint = status.get("setPoint", {})

        if setpoint:
            try:
                return float(setpoint.get("value", 0))
            except (ValueError, TypeError):
                return None

        return None

    @property
    def hvac_mode(self) -> Optional[HVACMode]:
        """Return current operation mode."""
        if not self.coordinator.data:
            return None

        status = self.coordinator.data.get("status", {})
        mode = status.get("mode")

        if mode in SMARTHER_TO_HVAC_MODE:
            hvac_mode = SMARTHER_TO_HVAC_MODE[mode]

            # Handle cooling function
            function = status.get("function", THERMOSTAT_FUNCTION_HEATING)
            if function == THERMOSTAT_FUNCTION_COOLING and hvac_mode == HVACMode.HEAT:
                return HVACMode.COOL

            return hvac_mode

        return None

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode."""
        if not self.coordinator.data:
            return None

        status = self.coordinator.data.get("status", {})
        return status.get("mode")

    @property
    def hvac_action(self) -> Optional[str]:
        """Return the current running hvac operation."""
        if not self.coordinator.data:
            return None

        status = self.coordinator.data.get("status", {})
        load_state = status.get("loadState")
        function = status.get("function", THERMOSTAT_FUNCTION_HEATING)

        if load_state == LOAD_STATE_ACTIVE:
            if function == THERMOSTAT_FUNCTION_HEATING:
                return "heating"
            elif function == THERMOSTAT_FUNCTION_COOLING:
                return "cooling"

        return "idle"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        status = self.coordinator.data.get("status", {})
        attributes = {
            ATTR_PLANT_ID: self.coordinator.plant_id,
            ATTR_MODULE_ID: self.coordinator.module_id,
            ATTR_DEVICE_TYPE: "chronothermostat",
        }

        # Add status information
        if "function" in status:
            attributes["function"] = status["function"]
        if "loadState" in status:
            attributes[ATTR_LOAD_STATE] = status["loadState"]
        if "activationTime" in status:
            attributes[ATTR_ACTIVATION_TIME] = status["activationTime"]
        if "temperatureFormat" in status:
            attributes[ATTR_TEMPERATURE_FORMAT] = status["temperatureFormat"]
        if "time" in status:
            attributes["thermostat_time"] = status["time"]

        # Add program information
        programs = status.get("programs", [])
        if programs:
            attributes[ATTR_PROGRAMS] = programs
            attributes[ATTR_PROGRAM_NUMBER] = programs[0].get("number")

        # Add humidity if available
        hygrometer = status.get("hygrometer", {})
        humidity_measures = hygrometer.get("measures", [])
        if humidity_measures:
            latest_humidity = humidity_measures[-1]
            try:
                attributes["current_humidity"] = float(latest_humidity.get("value", 0))
            except (ValueError, TypeError):
                pass

        # Add error information if available
        if self.coordinator.error_info:
            attributes.update(self.coordinator.error_info)

        return attributes

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            await self.coordinator.async_set_target_temperature(temperature)
        except SmartherAPIError as err:
            _LOGGER.error("Error setting temperature: %s", err)
            raise err

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode not in self.hvac_modes:
            _LOGGER.error("Unsupported HVAC mode: %s", hvac_mode)
            return

        # Map HA HVAC mode to Smarther mode
        if hvac_mode == HVACMode.OFF:
            smarther_mode = THERMOSTAT_MODE_OFF
        elif hvac_mode == HVACMode.AUTO:
            smarther_mode = THERMOSTAT_MODE_AUTOMATIC
        elif hvac_mode in (HVACMode.HEAT, HVACMode.COOL):
            smarther_mode = THERMOSTAT_MODE_MANUAL
        else:
            _LOGGER.error("Cannot map HVAC mode %s to Smarther mode", hvac_mode)
            return

        try:
            await self.coordinator.async_set_hvac_mode(smarther_mode)
        except SmartherAPIError as err:
            _LOGGER.error("Error setting HVAC mode: %s", err)
            raise err

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes:
            _LOGGER.error("Unsupported preset mode: %s", preset_mode)
            return

        try:
            await self.coordinator.async_set_preset_mode(preset_mode)
        except SmartherAPIError as err:
            _LOGGER.error("Error setting preset mode: %s", err)
            raise err
