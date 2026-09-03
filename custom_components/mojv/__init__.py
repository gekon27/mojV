"""mojV Home Assistant integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import MojVClient
from .const import (
    CONF_DEMO_STUDENTS,
    CONF_MODE,
    DEFAULT_DEMO_STUDENTS,
    DOMAIN,
    MODE_DEMO,
    PLATFORMS,
)
from .coordinator import MojVCoordinator
from .notifications import MojVNotificationManager
from .panel import async_register_school_panel, async_unregister_school_panel

DATA_NOTIFIERS = f"{DOMAIN}_notifiers"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up mojV from a config entry."""
    mode = entry.data.get(CONF_MODE, MODE_DEMO)
    client = MojVClient(
        mode=mode,
        demo_students=int(entry.data.get(CONF_DEMO_STUDENTS, DEFAULT_DEMO_STUDENTS)),
    )
    coordinator = MojVCoordinator(hass, client)
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
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if not hass.data.get(DOMAIN):
            async_unregister_school_panel(hass)
    return unloaded
