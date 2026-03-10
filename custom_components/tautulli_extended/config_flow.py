"""Config flow for Tautulli Extended."""
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_URL, DOMAIN


class TautulliExtendedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tautulli Extended."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            api_key = user_input[CONF_API_KEY]

            # Use URL as unique ID to prevent duplicates for same server
            await self.async_set_unique_id(url)
            self._abort_if_unique_id_configured()

            # Validate connection by calling get_tautulli_info
            if await self._test_connection(url, api_key):
                return self.async_create_entry(
                    title="Tautulli Extended",
                    data={CONF_URL: url, CONF_API_KEY: api_key},
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def _test_connection(self, url: str, api_key: str) -> bool:
        """Test if we can connect to Tautulli."""
        session = async_get_clientsession(self.hass)
        try:
            resp = await session.get(
                f"{url}/api/v2",
                params={"apikey": api_key, "cmd": "get_tautulli_info"},
                timeout=aiohttp.ClientTimeout(total=10),
            )
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            return data.get("response", {}).get("result") == "success"
        except (aiohttp.ClientError, TimeoutError):
            return False
