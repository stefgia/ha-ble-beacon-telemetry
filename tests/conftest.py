"""Shared test helpers: fake adverts and a stand-in for HA's Bluetooth subscription."""

from __future__ import annotations

import time
from collections.abc import Callable, Generator
from unittest.mock import MagicMock, patch

import pytest
from bleak.backends.device import BLEDevice
from homeassistant.components.bluetooth import BluetoothChange, BluetoothServiceInfoBleak

# Tests and samples use only these MACs, never a real device's.
TEST_ADDRESSES = ("C0:FF:EE:00:12:34", "D0:0D:00:AB:CD:EF")
ADDRESS = TEST_ADDRESSES[0]
PROXY_A = "AA:00:00:00:00:01"
PROXY_B = "AA:00:00:00:00:02"


def advert(
    *,
    address: str = ADDRESS,
    name: str | None = None,
    service_data: dict[str, bytes] | None = None,
    manufacturer_data: dict[int, bytes] | None = None,
    source: str = PROXY_A,
    at: float | None = None,
) -> BluetoothServiceInfoBleak:
    """An advert as a proxy passes it on, heard `at` now by default."""
    return BluetoothServiceInfoBleak(
        name=name or "",
        address=address,
        rssi=-60,
        manufacturer_data=manufacturer_data or {},
        service_data=service_data or {},
        service_uuids=[],
        source=source,
        device=BLEDevice(address, name, None),
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
