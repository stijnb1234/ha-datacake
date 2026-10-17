"""Sensors for Datacake fields."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import DatacakeConfigEntry
from .const import DOMAIN
from .coordinator import DatacakeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DatacakeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    known: set[tuple[str, str]] = set()

    @callback
    def _add_new() -> None:
        new = []
        for dev_id, dev in coordinator.data.items():
            for field_name in dev["fields"]:
                if (dev_id, field_name) not in known:
                    known.add((dev_id, field_name))
                    new.append(DatacakeSensor(coordinator, dev_id, field_name))
        if new:
            async_add_entities(new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


def _coerce(value: Any) -> Any:
    """Datacake returns values as JSON-ish scalars; prefer numbers."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            f = float(value)
        except ValueError:
            return value
        return int(f) if f.is_integer() and "." not in value else f
    return value


class DatacakeSensor(CoordinatorEntity[DatacakeCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DatacakeCoordinator, dev_id: str, field: str) -> None:
        super().__init__(coordinator)
        self._dev_id = dev_id
        self._field = field
        self._attr_unique_id = f"{dev_id}_{field}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dev_id)},
            name=coordinator.data[dev_id]["name"],
            manufacturer="Datacake",
        )

    @property
    def _measurement(self) -> dict[str, Any] | None:
        dev = self.coordinator.data.get(self._dev_id)
        return dev["fields"].get(self._field) if dev else None

    @property
    def available(self) -> bool:
        return super().available and self._measurement is not None

    @property
    def name(self) -> str:
        m = self._measurement
        return (m and m["field"].get("verboseFieldName")) or self._field

    @property
    def native_value(self) -> Any:
        m = self._measurement
        return _coerce(m["value"]) if m else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        m = self._measurement
        if not m or not m.get("modified"):
            return {}
        modified: datetime | None = dt_util.parse_datetime(m["modified"])
        return {"last_modified": modified.isoformat() if modified else m["modified"]}
