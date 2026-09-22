"""HolyIOT BLE: battery and button for HolyIOT tags, read from HA's Bluetooth adverts."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .tag import HolyIotTag

PLATFORMS = [Platform.EVENT, Platform.SENSOR]

type HolyIotConfigEntry = ConfigEntry[HolyIotTag]


async def async_setup_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Start listening to the tag's adverts."""
    assert entry.unique_id is not None
    tag = HolyIotTag(hass, entry.unique_id, entry.title)
    entry.runtime_data = tag
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Start after the entities exist, so the replayed last advert reaches them.
    entry.async_on_unload(tag.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Stop listening."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
