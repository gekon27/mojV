"""Config flow for mojV."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import (
    MojVBrowserVerificationRequired,
    MojVCannotConnect,
    MojVInvalidAuth,
    MojVNoStudents,
    async_login,
    create_session,
)
from .const import (
    AUTH_BACKEND_HELPER,
    AUTH_BACKEND_HTTP,
    CONF_AUTH_BACKEND,
    CONF_DEMO_STUDENTS,
    CONF_LESSON_END_MINUTES,
    CONF_MEETING_LEAD_HOURS,
    CONF_MODE,
    CONF_NOTIFICATION_TYPES,
    CONF_NOTIFY_TARGETS,
    CONF_PASSWORD,
    CONF_QUIET_HOURS_ENABLED,
    CONF_QUIET_HOURS_END,
    CONF_QUIET_HOURS_START,
    CONF_SCHOOLWORK_LEAD_HOURS,
    CONF_USERNAME,
    DEFAULT_DEMO_STUDENTS,
    DEFAULT_LESSON_END_MINUTES,
    DEFAULT_MEETING_LEAD_HOURS,
    DEFAULT_NOTIFICATION_TYPES,
    DEFAULT_QUIET_HOURS_END,
    DEFAULT_QUIET_HOURS_START,
    DEFAULT_SCHOOLWORK_LEAD_HOURS,
    DOMAIN,
    MAX_DEMO_STUDENTS,
    MIN_DEMO_STUDENTS,
    MODE_DEMO,
    MODE_LIVE,
    NOTIFICATION_TYPES,
)
from .helper_gateway import (
    HelperGateway,
    HelperInvalidAuth,
    HelperRequestError,
    HelperUnavailable,
)

_LOGGER = logging.getLogger(__name__)
_TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"


class MojVConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a mojV config flow."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return mojV options flow."""
        return MojVOptionsFlow()

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

    async def _async_helper_login(
        self,
        username: str,
        password: str,
    ) -> tuple[dict, ...]:
        """Validate an account through the local browser helper."""
        gateway = HelperGateway(async_get_clientsession(self.hass))
        await gateway.async_health()
        return await gateway.async_account(username, password)

    async def async_step_live(self, user_input=None):
        """Validate credentials and create a live account entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = str(user_input[CONF_USERNAME]).strip()
            password = str(user_input[CONF_PASSWORD])
            backend = AUTH_BACKEND_HTTP
            students = None
            session = create_session()
            try:
                try:
                    students = await async_login(session, username, password)
                except MojVBrowserVerificationRequired:
                    backend = AUTH_BACKEND_HELPER
                    if not session.closed:
                        await session.close()
                    students = await self._async_helper_login(username, password)
            except MojVInvalidAuth:
                errors["base"] = "invalid_auth"
            except MojVNoStudents:
                errors["base"] = "no_students"
            except MojVCannotConnect:
                errors["base"] = "cannot_connect"
            except HelperInvalidAuth:
                errors["base"] = "invalid_auth"
            except HelperUnavailable:
                errors["base"] = "helper_required"
            except HelperRequestError as err:
                if str(err) == "no_students":
                    errors["base"] = "no_students"
                else:
                    _LOGGER.warning("Local browser helper login failed: %s", err)
                    errors["base"] = "helper_failed"
            except Exception:
                _LOGGER.exception("Unexpected live-login error")
                errors["base"] = "unknown"
            finally:
                if not session.closed:
                    await session.close()

            if students is not None and not errors:
                await self.async_set_unique_id(f"mojv_live:{username.lower()}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"mojV — {len(students)} dzieci",
                    data={
                        CONF_MODE: MODE_LIVE,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_AUTH_BACKEND: backend,
                    },
                )

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


class MojVOptionsFlow(config_entries.OptionsFlow):
    """Configure notification behavior without touching credentials."""

    async def async_step_init(self, user_input=None):
        """Manage notification options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = dict(self.config_entry.options)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NOTIFICATION_TYPES,
                    default=current.get(
                        CONF_NOTIFICATION_TYPES, list(DEFAULT_NOTIFICATION_TYPES)
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(NOTIFICATION_TYPES),
                        multiple=True,
                        translation_key="notification_types",
                    )
                ),
                vol.Optional(
                    CONF_NOTIFY_TARGETS,
                    default=current.get(CONF_NOTIFY_TARGETS, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="notify", multiple=True)
                ),
                vol.Required(
                    CONF_LESSON_END_MINUTES,
                    default=current.get(
                        CONF_LESSON_END_MINUTES, DEFAULT_LESSON_END_MINUTES
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Required(
                    CONF_SCHOOLWORK_LEAD_HOURS,
                    default=current.get(
                        CONF_SCHOOLWORK_LEAD_HOURS, DEFAULT_SCHOOLWORK_LEAD_HOURS
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=336)),
                vol.Required(
                    CONF_MEETING_LEAD_HOURS,
                    default=current.get(
                        CONF_MEETING_LEAD_HOURS, DEFAULT_MEETING_LEAD_HOURS
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=336)),
                vol.Required(
                    CONF_QUIET_HOURS_ENABLED,
                    default=current.get(CONF_QUIET_HOURS_ENABLED, False),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_QUIET_HOURS_START,
                    default=current.get(
                        CONF_QUIET_HOURS_START, DEFAULT_QUIET_HOURS_START
                    ),
                ): vol.All(str, vol.Match(_TIME_PATTERN)),
                vol.Required(
                    CONF_QUIET_HOURS_END,
                    default=current.get(
                        CONF_QUIET_HOURS_END, DEFAULT_QUIET_HOURS_END
                    ),
                ): vol.All(str, vol.Match(_TIME_PATTERN)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
