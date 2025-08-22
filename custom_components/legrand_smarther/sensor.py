"""Sensor platform for Legrand Smarther."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_PLANT_ID,
    ATTR_MODULE_ID,
    ATTR_LAST_UPDATE,
    CONF_ENABLE_EXTRA_SENSORS,
)
from .coordinator import SmartherDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Legrand Smarther sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    
    entities = [
        LegrandSmartherTemperatureSensor(coordinator),
        LegrandSmartherHumiditySensor(coordinator),
    ]
    
    # Add extra sensors if enabled
    enable_extra_sensors = config_entry.options.get(CONF_ENABLE_EXTRA_SENSORS, True)
    if enable_extra_sensors:
        entities.extend([
            LegrandSmartherSetpointSensor(coordinator),
            LegrandSmartherLastUpdateSensor(coordinator),
        ])
    
    async_add_entities(entities)


class LegrandSmartherSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Legrand Smarther sensors."""

    def __init__(
        self,
        coordinator: SmartherDataUpdateCoordinator,
        sensor_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
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
        
        # Add error information if available
        if self.coordinator.error_info:
            attributes.update(self.coordinator.error_info)
        
        return attributes


class LegrandSmartherTemperatureSensor(LegrandSmartherSensorBase):
    """Temperature sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, "temperature", "Temperature")
        
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> Optional[float]:
        """Return the temperature value."""
        if not self.coordinator.data:
            return None
        
        # Try to get from measures first (most recent reading)
        measures_data = self.coordinator.data.get("measures", {})
        thermometer = measures_data.get("thermometer", {})
        measures = thermometer.get("measures", [])
        
        if measures:
            latest_measure = measures[-1]
            try:
                return float(latest_measure.get("value", 0))
            except (ValueError, TypeError):
                pass
        
        # Fallback to status data
        status = self.coordinator.data.get("status", {})
        thermometer = status.get("thermometer", {})
        measures = thermometer.get("measures", [])
        
        if measures:
            latest_measure = measures[-1]
            try:
                return float(latest_measure.get("value", 0))
            except (ValueError, TypeError):
                pass
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes
        
        if self.coordinator.data:
            # Add timestamp information
            measures_data = self.coordinator.data.get("measures", {})
            thermometer = measures_data.get("thermometer", {})
            measures = thermometer.get("measures", [])
            
            if measures:
                latest_measure = measures[-1]
                attributes["timestamp"] = latest_measure.get("timeStamp")
                attributes["unit"] = latest_measure.get("unit", "C")
            
        return attributes


class LegrandSmartherHumiditySensor(LegrandSmartherSensorBase):
    """Humidity sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, "humidity", "Humidity")
        
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> Optional[float]:
        """Return the humidity value."""
        if not self.coordinator.data:
            return None
        
        # Try to get from measures first (most recent reading)
        measures_data = self.coordinator.data.get("measures", {})
        hygrometer = measures_data.get("hygrometer", {})
        measures = hygrometer.get("measures", [])
        
        if measures:
            latest_measure = measures[-1]
            try:
                return float(latest_measure.get("value", 0))
            except (ValueError, TypeError):
                pass
        
        # Fallback to status data
        status = self.coordinator.data.get("status", {})
        hygrometer = status.get("hygrometer", {})
        measures = hygrometer.get("measures", [])
        
        if measures:
            latest_measure = measures[-1]
            try:
                return float(latest_measure.get("value", 0))
            except (ValueError, TypeError):
                pass
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes
        
        if self.coordinator.data:
            # Add timestamp information
            measures_data = self.coordinator.data.get("measures", {})
            hygrometer = measures_data.get("hygrometer", {})
            measures = hygrometer.get("measures", [])
            
            if measures:
                latest_measure = measures[-1]
                attributes["timestamp"] = latest_measure.get("timeStamp")
                attributes["unit"] = latest_measure.get("unit", "%")
            
        return attributes


class LegrandSmartherSetpointSensor(LegrandSmartherSensorBase):
    """Setpoint sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the setpoint sensor."""
        super().__init__(coordinator, "setpoint", "Target Temperature")
        
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_entity_category = "diagnostic"

    @property
    def native_value(self) -> Optional[float]:
        """Return the setpoint value."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.get("status", {})
        setpoint = status.get("setPoint", {})
        
        if setpoint:
            try:
                return float(setpoint.get("value", 0))
            except (ValueError, TypeError):
                pass
        
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes
        
        if self.coordinator.data:
            status = self.coordinator.data.get("status", {})
            setpoint = status.get("setPoint", {})
            
            if setpoint:
                attributes["unit"] = setpoint.get("unit", "C")
                
            # Add mode information
            attributes["mode"] = status.get("mode")
            attributes["function"] = status.get("function")
            
        return attributes


class LegrandSmartherLastUpdateSensor(LegrandSmartherSensorBase):
    """Last update sensor for Legrand Smarther."""

    def __init__(self, coordinator: SmartherDataUpdateCoordinator) -> None:
        """Initialize the last update sensor."""
        super().__init__(coordinator, "last_update", "Last Update")
        
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = "diagnostic"

    @property
    def native_value(self) -> Optional[str]:
        """Return the last update timestamp."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get(ATTR_LAST_UPDATE)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes
        
        if self.coordinator.data:
            attributes["coordinator_last_update"] = self.coordinator.last_update_success_time
            
        return attributes