"""OAuth2 authentication for Legrand Smarther."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE_URL,
    OAUTH2_SCOPES,
    OAUTH2_TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class LegrandSmartherOAuth2Implementation(LocalOAuth2Implementation):
    """Legrand Smarther OAuth2 implementation."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
    ):
        """Initialize the OAuth2 implementation."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            client_secret,
            OAUTH2_AUTHORIZE_URL,
            OAUTH2_TOKEN_URL,
        )

    @property
    def default_scopes(self) -> list[str]:
        """Return the default scopes."""
        return OAUTH2_SCOPES

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Return extra authorize data."""
        return {"scope": " ".join(OAUTH2_SCOPES)}


async def async_get_oauth_implementation(
    hass: HomeAssistant, client_id: str, client_secret: str
) -> LegrandSmartherOAuth2Implementation:
    """Get the OAuth2 implementation."""
    return LegrandSmartherOAuth2Implementation(hass, client_id, client_secret)


async def async_setup_oauth(hass: HomeAssistant) -> None:
    """Set up OAuth2 for Legrand Smarther."""
    # OAuth2 implementations are now registered via application_credentials platform
    pass
