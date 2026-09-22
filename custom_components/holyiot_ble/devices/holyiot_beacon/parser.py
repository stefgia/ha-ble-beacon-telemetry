"""Decode the HolyIOT service data carried under UUID 0x5242.

The payload is 13 bytes:

    0      0x41
    1      battery, percent
    2-7    the tag's own MAC, most significant byte first
    8-9    unknown
    10     measurement type: 6 is a button, others are sensors this doesn't read
    11     1 for a few seconds after a long press (about 5 s), else 0.
           Short presses don't set it.
    12     unused by the button

Tags send it only in the scan response, so a proxy has to scan actively to hear it.
See README.md in this folder for how the tag behaves.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak


SERVICE_UUID = "00005242-0000-1000-8000-00805f9b34fb"
PAYLOAD_LENGTH = 13
MEASUREMENT_BUTTON = 6


@dataclass(frozen=True, slots=True)
class HolyIotReading:
    """What one advert says about a tag."""

    battery: int
    # None when the tag reports a measurement other than a button.
    pressed: bool | None


def parse_payload(address: str, payload: bytes) -> HolyIotReading | None:
    """Decode a 0x5242 payload, or return None if it isn't one from this tag."""
    if len(payload) != PAYLOAD_LENGTH:
        return None
    if payload[2:8] != bytes.fromhex(address.replace(":", "")):
        return None
    battery = payload[1]
    if battery > 100:
        return None
    pressed = payload[11] == 1 if payload[10] == MEASUREMENT_BUTTON else None
    return HolyIotReading(battery=battery, pressed=pressed)


def parse_service_info(service_info: BluetoothServiceInfoBleak) -> HolyIotReading | None:
    """Decode the HolyIOT data in an advert, if it has any."""
    if (payload := service_info.service_data.get(SERVICE_UUID)) is None:
        return None
    return parse_payload(service_info.address, payload)
