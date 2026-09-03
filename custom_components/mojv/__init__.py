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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up mojV from a config entry."""
    client = MojVClient(
        mode=entry.data.get(CONF_MODE, MODE_DEMO),
        demo_students=int(entry.data.get(CONF_DEMO_STUDENTS, DEFAULT_DEMO_STUDENTS)),
    )
    coordinator = MojVCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a mojV config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
