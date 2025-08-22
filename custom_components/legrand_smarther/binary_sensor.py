"""Binary sensor platform for Legrand Smarther."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_PLANT_ID,
    ATTR_MODULE_ID,
    LOAD_STATE_ACTIVE,
    THERMOSTAT_FUNCTION_HEATING,
    THERMOSTAT_FUNCTION_COOLING,
    CONF_ENABLE_EXTRA_SENSORS,
)
from .coordinator import SmartherDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Legrand Smarther binary sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = []
    
    # Add extra sensors if enabled
    enable_extra_sensors = config_entry.options.get(CONF_ENABLE_EXTRA_SENSORS, True)
    if enable_extra_sensors:
        entities.extend([
            LegrandSmartherHeatingSensor(coordinator),
            LegrandSmartherCoolingSensor(coordinator),
        ])
    
    if entities:
        async_add_entities(entities)


class LegrandSmartherBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Base class for Legrand Smarther binary sensors."""

    def __init__(
        self,
        coordinator: SmartherDataUpdateCoordinator,
        sensor_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{DOMAIN}_{coordinator.module_id}_{sensor_type}"
        self._attr_name = f"{coordinator.module_name} {name_suffix}"

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
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = {
            ATTR_PLANT_ID: self.coordinator.plant_id,
            ATTR_MODULE_ID: self.coordinator.module_id,
        }
        
        if self.coordinator.data:
            status = self.coordinator.data.get("status", {})
            attributes["load_state"] = status.get("loadState")
            attributes["function"] = status.get("function")
            attributes["mode"] = status.get("mode")
        
        # Add error information if available
        if self.coordinator.error_info:
            attributes.update(self.coordinator.error_info)
        
        return attributes


class LegrandSmartherHeatingSensor(LegrandSmartherBinarySensorBase):
    """Heating binary sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the heating sensor."""
        super().__init__(coordinator, "heating", "Heating")
        
        self._attr_device_class = BinarySensorDeviceClass.HEAT
        self._attr_entity_category = "diagnostic"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if heating is active."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        load_state = status.get("loadState")
        function = status.get("function", THERMOSTAT_FUNCTION_HEATING)
        
        # Heating is active if load state is active and function is heating
        return (
            load_state == LOAD_STATE_ACTIVE
            and function == THERMOSTAT_FUNCTION_HEATING
        )

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        if self.is_on:
            return "mdi:radiator"
        return "mdi:radiator-off"


class LegrandSmartherCoolingSensor(LegrandSmartherBinarySensorBase):
    """Cooling binary sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the cooling sensor."""
        super().__init__(coordinator, "cooling", "Cooling")
        
        self._attr_device_class = BinarySensorDeviceClass.COLD
        self._attr_entity_category = "diagnostic"

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if cooling is active."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        load_state = status.get("loadState")
        function = status.get("function", THERMOSTAT_FUNCTION_HEATING)
        
        # Cooling is active if load state is active and function is cooling
        return (
            load_state == LOAD_STATE_ACTIVE
            and function == THERMOSTAT_FUNCTION_COOLING
        )

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        if self.is_on:
            return "mdi:snowflake"
        return "mdi:snowflake-off"