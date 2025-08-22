"""The Legrand Smarther integration."""
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .auth import async_setup_oauth
from .const import DOMAIN, ATTR_PLANT_ID, ATTR_MODULE_ID
from .coordinator import SmartherDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Set up the Legrand Smarther component."""
    hass.data.setdefault(DOMAIN, {})
    
    # Set up OAuth2
    await async_setup_oauth(hass)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Legrand Smarther from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Check if this is a module entry (has plant_id and module_id)
    if ATTR_PLANT_ID in entry.data and ATTR_MODULE_ID in entry.data:
        # This is a module-specific entry
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
        
        session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
        
        plant_id = entry.data[ATTR_PLANT_ID]
        module_id = entry.data[ATTR_MODULE_ID]
        module_name = entry.data.get("module_name", f"Module {module_id}")
        
        # Get scan interval from options
        scan_interval = entry.options.get("scan_interval", 60)
        
        coordinator = SmartherDataUpdateCoordinator(
            hass, session, plant_id, module_id, module_name, scan_interval
        )
        
        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()
        
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "session": session,
        }
        
        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Register update listener for options
        entry.async_on_unload(entry.add_update_listener(async_update_options))
        
        return True
    else:
        # This is the main integration entry (OAuth2 only)
        _LOGGER.debug("Main integration entry setup completed")
        return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id in hass.data[DOMAIN]:
        # This is a module entry
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
        
        return unload_ok
    else:
        # This is the main integration entry
        return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    # Clean up any stored data
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id, None)