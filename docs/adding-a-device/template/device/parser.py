"""Decode DEVICE NAME's data.

TODO: document the byte layout here and in README.md:

    0      ...
    1      battery, percent
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

SERVICE_UUID = "0000xxxx-0000-1000-8000-00805f9b34fb"  # TODO


@dataclass(frozen=True, slots=True)
class Reading:
    """What one advert says. TODO: one field per value."""

    battery: int


def parse_payload(address: str, payload: bytes) -> Reading | None:
    """Decode a payload, or return None if it isn't one this device sends.

    Check everything you can (length, fixed bytes, the MAC if the payload
    repeats it, value ranges), so this device never claims another's data.
    """
    if len(payload) != 2:  # TODO
        return None
    return Reading(battery=payload[1])


def parse_service_info(service_info: BluetoothServiceInfoBleak) -> Reading | None:
    """Decode the device's data in an advert, if it has any."""
    if (payload := service_info.service_data.get(SERVICE_UUID)) is None:
        return None
    return parse_payload(service_info.address, payload)
