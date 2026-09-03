"""DataUpdateCoordinator for mojV."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import MojVClient, MojVClientError
from .const import DEMO_UPDATE_INTERVAL, DOMAIN, LIVE_UPDATE_INTERVAL
from .models import AccountSnapshot

_LOGGER = logging.getLogger(__name__)


class MojVCoordinator(DataUpdateCoordinator[AccountSnapshot]):
    """Coordinate one account containing one or many students."""

    def __init__(self, hass: HomeAssistant, client: MojVClient, *, live: bool) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=LIVE_UPDATE_INTERVAL if live else DEMO_UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> AccountSnapshot:
        try:
            return await self.client.async_fetch()
        except MojVClientError as err:
            raise UpdateFailed(str(err)) from err
