"""Config flow for mojV."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_DEMO_STUDENTS,
    CONF_MODE,
    DEFAULT_DEMO_STUDENTS,
    DOMAIN,
    MAX_DEMO_STUDENTS,
    MIN_DEMO_STUDENTS,
    MODE_DEMO,
)


class MojVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a mojV config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the initial demo entry used to validate HACS and HA plumbing."""
        if user_input is not None:
            count = int(user_input[CONF_DEMO_STUDENTS])
            await self.async_set_unique_id("mojv_demo")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"mojV — test ({count} dzieci)",
                data={CONF_MODE: MODE_DEMO, CONF_DEMO_STUDENTS: count},
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEMO_STUDENTS, default=DEFAULT_DEMO_STUDENTS
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_DEMO_STUDENTS, max=MAX_DEMO_STUDENTS),
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
