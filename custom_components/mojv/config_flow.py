"""Config flow for mojV."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .auth import (
    MojVBrowserVerificationRequired,
    MojVCannotConnect,
    MojVInvalidAuth,
    MojVNoStudents,
    async_login,
    create_session,
)
from .const import (
    CONF_DEMO_STUDENTS,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_DEMO_STUDENTS,
    DOMAIN,
    MAX_DEMO_STUDENTS,
    MIN_DEMO_STUDENTS,
    MODE_DEMO,
    MODE_LIVE,
)

_LOGGER = logging.getLogger(__name__)


class MojVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a mojV config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Choose live or demo setup."""
        if user_input is not None:
            if user_input[CONF_MODE] == MODE_DEMO:
                return await self.async_step_demo()
            return await self.async_step_live()

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=MODE_LIVE): vol.In(
                    {
                        MODE_LIVE: "Konto szkolne",
                        MODE_DEMO: "Tryb demonstracyjny",
                    }
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_demo(self, user_input=None):
        """Configure deterministic demo data."""
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
        return self.async_show_form(step_id="demo", data_schema=schema)

    async def async_step_live(self, user_input=None):
        """Validate credentials and create a live account entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = str(user_input[CONF_USERNAME]).strip()
            password = str(user_input[CONF_PASSWORD])
            session = create_session()
            try:
                students = await async_login(session, username, password)
            except MojVInvalidAuth:
                errors["base"] = "invalid_auth"
            except MojVBrowserVerificationRequired:
                errors["base"] = "browser_verification_required"
            except MojVNoStudents:
                errors["base"] = "no_students"
            except MojVCannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected live-login error")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"mojv_live:{username.lower()}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"mojV — {len(students)} dzieci",
                    data={
                        CONF_MODE: MODE_LIVE,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )
            finally:
                if not session.closed:
                    await session.close()

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="live",
            data_schema=schema,
            errors=errors,
        )
