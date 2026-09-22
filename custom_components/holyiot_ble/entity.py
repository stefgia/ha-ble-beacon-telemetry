"""Base entity: every entity sits on the tag's device, identified by its Bluetooth MAC."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity

from .tag import HolyIotTag


class HolyIotEntity(Entity):
    """An entity of one HolyIOT tag."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    # Unique per tag; set by each subclass.
    _key: str

    def __init__(self, tag: HolyIotTag) -> None:
        """Attach to the tag's device.

        The Bluetooth connection identifies the device. Home Assistant keeps one
        device per integration, and links devices that share a connection, so
        this device is linked to any other integration's device for the same tag
        (Bermuda's, for example).
        """
        self.tag = tag
        self._attr_unique_id = f"{tag.address}_{self._key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, tag.address)},
            manufacturer="HolyIOT",
            name=tag.name,
        )
