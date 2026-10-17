"""Map Datacake's free-text field units to Home Assistant units/device classes."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass as C
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)

# normalised unit text -> (HA unit, device class or None)
_KNOWN: dict[str, tuple[str, C | None]] = {
    "°c": (UnitOfTemperature.CELSIUS, C.TEMPERATURE),
    "celsius": (UnitOfTemperature.CELSIUS, C.TEMPERATURE),
    "°f": (UnitOfTemperature.FAHRENHEIT, C.TEMPERATURE),
    "dbm": (SIGNAL_STRENGTH_DECIBELS_MILLIWATT, C.SIGNAL_STRENGTH),
    "db": (SIGNAL_STRENGTH_DECIBELS, C.SIGNAL_STRENGTH),
    "fahrenheit": (UnitOfTemperature.FAHRENHEIT, C.TEMPERATURE),
    "v": (UnitOfElectricPotential.VOLT, C.VOLTAGE),
    "mv": (UnitOfElectricPotential.MILLIVOLT, C.VOLTAGE),
    "a": (UnitOfElectricCurrent.AMPERE, C.CURRENT),
    "ma": (UnitOfElectricCurrent.MILLIAMPERE, C.CURRENT),
    "w": (UnitOfPower.WATT, C.POWER),
    "kw": (UnitOfPower.KILO_WATT, C.POWER),
    "hpa": (UnitOfPressure.HPA, C.PRESSURE),
    "mbar": (UnitOfPressure.MBAR, C.PRESSURE),
    "bar": (UnitOfPressure.BAR, C.PRESSURE),
    "pa": (UnitOfPressure.PA, C.PRESSURE),
    "kpa": (UnitOfPressure.KPA, C.PRESSURE),
    "s": (UnitOfTime.SECONDS, C.DURATION),
    "min": (UnitOfTime.MINUTES, C.DURATION),
    "h": (UnitOfTime.HOURS, C.DURATION),
}

_PERCENT = {"%", "percent"}


def resolve_unit(
    raw: str | None, field_name: str, verbose_name: str | None
) -> tuple[str | None, C | None]:
    """Return (unit, device_class). Unknown units pass through unchanged."""
    if not raw or not raw.strip():
        return None, None
    unit = raw.strip()
    # U+2103 / U+2109 are single-codepoint "℃" / "℉"
    key = unit.lower().replace("\u2103", "°c").replace("\u2109", "°f")

    if key in _PERCENT:
        hint = f"{field_name} {verbose_name or ''}".lower()
        if "batt" in hint:
            return PERCENTAGE, C.BATTERY
        if "hum" in hint:
            return PERCENTAGE, C.HUMIDITY
        if "moist" in hint:
            return PERCENTAGE, C.MOISTURE
        return PERCENTAGE, None

    if key in _KNOWN:
        return _KNOWN[key]
    return unit, None
