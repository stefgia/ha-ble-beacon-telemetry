"""Shared test data, and a stand-in for Home Assistant's Bluetooth subscription."""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from unittest.mock import MagicMock, patch

import pytest
from bleak.backends.device import BLEDevice
from homeassistant.components.bluetooth import BluetoothChange, BluetoothServiceInfoBleak

from custom_components.holyiot_ble.const import SERVICE_UUID

ADDRESS = "C0:FF:EE:00:12:34"
TITLE = "HolyIOT 1234"
PROXY_A = "AA:00:00:00:00:01"
PROXY_B = "AA:00:00:00:00:02"
# 79 % battery, button type, not pressed.
PAYLOAD = bytes.fromhex("414fc0ffee0012340206060000")
IBEACON = bytes.fromhex("0215fda50693a4e24fb1afcfc6eb07647825271b4cb9c9")


def payload(*, battery: int = 79, pressed: bool = False) -> bytes:
    """PAYLOAD with another battery level or button state."""
    return PAYLOAD[:1] + bytes([battery]) + PAYLOAD[2:11] + bytes([pressed]) + PAYLOAD[12:]


def service_info(
    data: bytes = PAYLOAD, *, source: str = PROXY_A, at: float | None = None
) -> BluetoothServiceInfoBleak:
    """An advert from the tag as a proxy passes it on, heard `at` now by default."""
    return BluetoothServiceInfoBleak(
        name="Holy-IOT-S",
        address=ADDRESS,
        rssi=-60,
        manufacturer_data={76: IBEACON},
        service_data={SERVICE_UUID: data},
        service_uuids=[],
        source=source,
        device=BLEDevice(ADDRESS, "Holy-IOT-S", None),
        advertisement=None,
        connectable=False,
        time=time.monotonic() if at is None else at,
        tx_power=None,
    )


class FakeBluetooth:
    """Stands in for HA's Bluetooth subscription: records callbacks, delivers adverts."""

    def __init__(self, register: MagicMock) -> None:
        """Take over `register`, the patched async_register_callback."""
        self.register = register
        self.callbacks: list[Callable[..., None]] = []
        register.side_effect = self._subscribe

    def _subscribe(self, hass, callback, matcher, mode) -> Callable[[], None]:
        self.callbacks.append(callback)
        return lambda: self.callbacks.remove(callback)

    def deliver(self, info: BluetoothServiceInfoBleak) -> None:
        """Hand an advert to every tag that has subscribed, as HA would."""
        for callback in list(self.callbacks):
            callback(info, BluetoothChange.ADVERTISEMENT)


@pytest.fixture
def bluetooth() -> Generator[FakeBluetooth]:
    """Replace HA's Bluetooth subscription, so no Bluetooth manager is needed."""
    with patch("custom_components.holyiot_ble.tag.async_register_callback") as register:
        yield FakeBluetooth(register)
