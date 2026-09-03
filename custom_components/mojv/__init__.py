"""mojV Home Assistant integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import MojVClient
from .const import (
    AUTH_BACKEND_HELPER,
    AUTH_BACKEND_HTTP,
    CONF_AUTH_BACKEND,
    CONF_DEMO_STUDENTS,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_DEMO_STUDENTS,
    DOMAIN,
    MODE_DEMO,
    PLATFORMS,
)
from .coordinator import MojVCoordinator
from .helper_gateway import HelperGateway
from .migration import migrate_entry_data
from .notifications import MojVNotificationManager
from .panel import async_register_school_panel, async_unregister_school_panel

DATA_NOTIFIERS = f"{DOMAIN}_notifiers"


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate an older mojV config entry to the current schema."""
    version, data = migrate_entry_data(entry.version, dict(entry.data))
    if version != entry.version or data != dict(entry.data):
        hass.config_entries.async_update_entry(entry, data=data, version=version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up mojV from a config entry."""
    mode = entry.data.get(CONF_MODE, MODE_DEMO)
    auth_backend = str(entry.data.get(CONF_AUTH_BACKEND, AUTH_BACKEND_HTTP))
    helper_gateway = None
    if mode != MODE_DEMO and auth_backend == AUTH_BACKEND_HELPER:
        helper_gateway = HelperGateway(async_get_clientsession(hass))

    client = MojVClient(
        mode=mode,
        demo_students=int(entry.data.get(CONF_DEMO_STUDENTS, DEFAULT_DEMO_STUDENTS)),
        username=str(entry.data.get(CONF_USERNAME, "")),
        password=str(entry.data.get(CONF_PASSWORD, "")),
        auth_backend=auth_backend,
        helper_gateway=helper_gateway,
    )
    coordinator = MojVCoordinator(hass, client, live=mode != MODE_DEMO)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await async_register_school_panel(hass)

    notifier = MojVNotificationManager(
        hass,
        coordinator,
        entry.entry_id,
        demo_mode=mode == MODE_DEMO,
    )
    await notifier.async_start()
    hass.data.setdefault(DATA_NOTIFIERS, {})[entry.entry_id] = notifier

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a mojV config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        notifier = hass.data.get(DATA_NOTIFIERS, {}).pop(entry.entry_id, None)
        if notifier:
            notifier.async_stop()
        coordinator = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if coordinator:
            await coordinator.client.async_close()
        if not hass.data.get(DOMAIN):
            async_unregister_school_panel(hass)
    return unloaded
