"""HolyIOT BLE: entities for HolyIOT tags, read from Home Assistant's Bluetooth adverts."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_DEVICE
from .devices import get_device
from .tag import Tag

PLATFORMS = [Platform.EVENT, Platform.SENSOR]

type HolyIotConfigEntry = ConfigEntry[Tag]


async def async_setup_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Start listening to the tag's adverts."""
    assert entry.unique_id is not None
    if (device := get_device(entry.data[CONF_DEVICE])) is None:
        raise ConfigEntryError(f"Unknown device model {entry.data[CONF_DEVICE]!r}")
    tag = Tag(hass, entry.unique_id, entry.title, device)
    entry.runtime_data = tag
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Start after the entities exist, so the replayed last advert reaches them.
    entry.async_on_unload(tag.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Stop listening."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: HolyIotConfigEntry) -> bool:
    """Bring older config entries up to date."""
    if entry.version == 1:
        # Version 1 supported only the button tag and stored no model.
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_DEVICE: "holyiot_beacon"}, version=2
        )
    return True
