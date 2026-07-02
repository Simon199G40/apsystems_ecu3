"""The APSystems ECU-3 integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import APSystemsECU3Coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type APSystemsECU3ConfigEntry = ConfigEntry[APSystemsECU3Coordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: APSystemsECU3ConfigEntry,
) -> bool:
    """Set up APSystems ECU-3 from a config entry."""

    coordinator = APSystemsECU3Coordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(
        entry.add_update_listener(_async_update_listener)
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: APSystemsECU3ConfigEntry,
) -> bool:
    """Unload a config entry."""

    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )


async def _async_update_listener(
    hass: HomeAssistant,
    entry: APSystemsECU3ConfigEntry,
) -> None:
    """Reload the config entry when its options are updated."""

    await hass.config_entries.async_reload(entry.entry_id)
