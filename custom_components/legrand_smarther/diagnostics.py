"""Diagnostics support for Legrand Smarther."""

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> Dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN].get(config_entry.entry_id, {})
    coordinator = data.get("coordinator")

    if not coordinator:
        return {"error": "No coordinator found for this entry"}

    diagnostics = {
        "config_entry": {
            "title": config_entry.title,
            "domain": config_entry.domain,
            "version": config_entry.version,
            "options": config_entry.options,
            "unique_id": config_entry.unique_id,
        },
        "coordinator": {
            "name": coordinator.name,
            "update_interval": coordinator.update_interval.total_seconds(),
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": (
                coordinator.last_update_success_time.isoformat()
                if coordinator.last_update_success_time
                else None
            ),
            "available": coordinator.available,
            "plant_id": coordinator.plant_id,
            "module_id": coordinator.module_id,
            "module_name": coordinator.module_name,
        },
        "data": _redact_sensitive_data(coordinator.data),
        "error_info": coordinator.error_info,
    }

    # Add OAuth session info (without tokens)
    session = data.get("session")
    if session:
        diagnostics["oauth_session"] = {
            "implementation_domain": getattr(
                session.implementation, "domain", "unknown"
            ),
            "token_valid": await session.async_ensure_token_valid() is None,
        }

    return diagnostics


def _redact_sensitive_data(data: Any) -> Any:
    """Redact sensitive data from diagnostics."""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if key in ("access_token", "refresh_token", "token", "authorization"):
                redacted[key] = "**REDACTED**"
            elif key in ("plant_id", "module_id") and isinstance(value, str):
                # Partially redact IDs for privacy
                redacted[key] = (
                    f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "**REDACTED**"
                )
            else:
                redacted[key] = _redact_sensitive_data(value)
        return redacted
    elif isinstance(data, list):
        return [_redact_sensitive_data(item) for item in data]
    else:
        return data
