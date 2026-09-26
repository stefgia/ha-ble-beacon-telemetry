"""BLE Beacon Telemetry: entities for what Bluetooth beacons broadcast, read from Home Assistant's adverts."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import CONF_DEVICE
from .devices import get_device
from .beacon import Beacon

PLATFORMS = [Platform.EVENT, Platform.SENSOR]

type BeaconConfigEntry = ConfigEntry[Beacon]


async def async_setup_entry(hass: HomeAssistant, entry: BeaconConfigEntry) -> bool:
    """Start listening to the beacon's adverts."""
    assert entry.unique_id is not None
    if (device := get_device(entry.data[CONF_DEVICE])) is None:
        raise ConfigEntryError(f"Unknown device model {entry.data[CONF_DEVICE]!r}")
    beacon = Beacon(hass, entry.unique_id, entry.title, device)
    entry.runtime_data = beacon
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Start after the entities exist, so the replayed last advert reaches them.
    entry.async_on_unload(beacon.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BeaconConfigEntry) -> bool:
    """Stop listening."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

