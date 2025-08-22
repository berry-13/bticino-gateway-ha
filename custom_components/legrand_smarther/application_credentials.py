"""Application credentials platform for Legrand Smarther integration."""

from homeassistant.components.application_credentials import (
    AuthImplementation,
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, OAUTH2_AUTHORIZE_URL, OAUTH2_SCOPES, OAUTH2_TOKEN_URL


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return auth implementation for application credentials."""
    return LegrandSmartherLocalOAuth2Implementation(
        hass,
        auth_domain,
        credential,
        authorization_server=AuthorizationServer(
            authorize_url=OAUTH2_AUTHORIZE_URL,
            token_url=OAUTH2_TOKEN_URL,
        ),
    )


class LegrandSmartherLocalOAuth2Implementation(AuthImplementation):
    """Local OAuth2 implementation for Legrand Smarther."""

    @property
    def default_scopes(self) -> list[str]:
        """Return the default scopes."""
        return OAUTH2_SCOPES

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Return extra authorize data."""
        return {"scope": " ".join(OAUTH2_SCOPES)}


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "developer_dashboard_url": "https://developer.legrand.com/",
        "redirect_url": "https://my.home-assistant.io/redirect/oauth",
        "more_info_url": "https://github.com/berry-13/bticino-gateway-ha#setup",
    }