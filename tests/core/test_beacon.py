"""Unit tests for Beacon, the per-beacon runtime, with a fake device and no Home Assistant."""

from unittest.mock import MagicMock

from homeassistant.components.bluetooth import BluetoothScanningMode

from custom_components.ble_beacon_telemetry.beacon import Beacon

from ..conftest import ADDRESS, FakeBluetooth
from .fake_device import FakeDevice, fake_advert


def started_beacon(device: FakeDevice | None = None) -> Beacon:
    beacon = Beacon(MagicMock(), ADDRESS, "Fake Tag 1234", device or FakeDevice())
    beacon.async_start()
    return beacon


def test_listens_to_this_beacon_only(bluetooth: FakeBluetooth) -> None:
    started_beacon()
    _, _, matcher, mode = bluetooth.register.call_args.args
    assert matcher == {"address": ADDRESS, "connectable": False}
    assert mode is BluetoothScanningMode.ACTIVE


def test_passive_when_the_device_needs_no_scan_response(bluetooth: FakeBluetooth) -> None:
    device = FakeDevice()
    device.needs_active_scan = False
    started_beacon(device)
    assert bluetooth.register.call_args.args[3] is BluetoothScanningMode.PASSIVE


def test_value_listeners_hear_changes_only(bluetooth: FakeBluetooth) -> None:
    beacon = started_beacon()
    listener = MagicMock()
    beacon.async_on_value("level", listener)
    for level in (50, 50, 60):
        bluetooth.deliver(fake_advert(level))
    assert beacon.values == {"level": 60}
    assert listener.call_count == 2


def test_event_listeners_get_the_event_type(bluetooth: FakeBluetooth) -> None:
    beacon = started_beacon()
    listener = MagicMock()
    beacon.async_on_event("ping", listener)
    bluetooth.deliver(fake_advert(ping=True))
    listener.assert_called_once_with("ping")


def test_unsubscribed_listener_is_not_called(bluetooth: FakeBluetooth) -> None:
    beacon = started_beacon()
    listener = MagicMock()
    beacon.async_on_value("level", listener)()
    bluetooth.deliver(fake_advert())
    listener.assert_not_called()
