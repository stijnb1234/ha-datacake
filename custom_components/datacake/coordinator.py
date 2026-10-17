"""Data update coordinator."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DatacakeAuthError, DatacakeClient, DatacakeError
from .const import CONF_WORKSPACE_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DatacakeCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch all devices + current measurements; keyed by device id."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: DatacakeClient,
        interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self.workspace_id: str = entry.data[CONF_WORKSPACE_ID]

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.client.get_devices(self.workspace_id)
        except DatacakeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except DatacakeError as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, dict[str, Any]] = {}
        for dev in devices:
            result[dev["id"]] = {
                "name": dev["verboseName"],
                "fields": {
                    m["field"]["fieldName"]: m
                    for m in dev.get("currentMeasurements") or []
                    if m.get("field")
                },
            }
        return result
