"""Base entity: every entity sits on the beacon's device, identified by its Bluetooth MAC."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .beacon import Beacon


class BeaconEntity(Entity):
    """An entity of one beacon, described by its device model."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, beacon: Beacon, description: EntityDescription) -> None:
        """Attach to the beacon's device.

        The Bluetooth connection identifies the device. Home Assistant keeps one
        device per integration, and links devices that share a connection, so
        this device is linked to any other integration's device for the same beacon
        (Bermuda's, for example).
        """
        self.beacon = beacon
        self.entity_description = description
        self._attr_unique_id = f"{beacon.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, beacon.address)},
            manufacturer=beacon.device.manufacturer,
            model=beacon.device.name,
            name=beacon.name,
        )
