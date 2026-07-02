"""Diagnostics support for APSystems ECU-3."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOST

TO_REDACT = {
    CONF_HOST,
    "mac_address",
    "ecu_id",
    "serial_number",
    "ip_address",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    coordinator = entry.runtime_data

    return {
        "entry": async_redact_data(
            dict(entry.as_dict()),
            TO_REDACT,
        ),
        "data": async_redact_data(
            coordinator.data,
            TO_REDACT,
        ),
    }