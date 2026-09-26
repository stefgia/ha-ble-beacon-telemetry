"""Every supported device model.

To add a model, create its folder next to this file and add it to DEVICES.
"""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from ..device import Device
from .holyiot_button_tag import HolyIotButtonTag

DEVICES: tuple[Device, ...] = (HolyIotButtonTag(),)


def get_device(device_id: str) -> Device | None:
    """The model with this id, if there is one."""
    return next((device for device in DEVICES if device.id == device_id), None)


def find_device(service_info: BluetoothServiceInfoBleak) -> Device | None:
    """The first model that claims this advert, if any."""
    return next((device for device in DEVICES if device.matches(service_info)), None)
