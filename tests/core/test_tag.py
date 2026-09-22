"""Unit tests for Tag, the per-tag runtime, with a fake device and no Home Assistant."""

from unittest.mock import MagicMock

from homeassistant.components.bluetooth import BluetoothScanningMode

from custom_components.holyiot_ble.tag import Tag

from ..conftest import ADDRESS, FakeBluetooth
from .fake_device import FakeDevice, fake_advert


def started_tag(device: FakeDevice | None = None) -> Tag:
    tag = Tag(MagicMock(), ADDRESS, "Fake Tag 1234", device or FakeDevice())
    tag.async_start()
    return tag


def test_listens_to_this_tag_only(bluetooth: FakeBluetooth) -> None:
    started_tag()
    _, _, matcher, mode = bluetooth.register.call_args.args
    assert matcher == {"address": ADDRESS, "connectable": False}
    assert mode is BluetoothScanningMode.ACTIVE


def test_passive_when_the_device_needs_no_scan_response(bluetooth: FakeBluetooth) -> None:
    device = FakeDevice()
    device.needs_active_scan = False
    started_tag(device)
    assert bluetooth.register.call_args.args[3] is BluetoothScanningMode.PASSIVE


def test_value_listeners_hear_changes_only(bluetooth: FakeBluetooth) -> None:
    tag = started_tag()
    listener = MagicMock()
    tag.async_on_value("level", listener)
    for level in (50, 50, 60):
        bluetooth.deliver(fake_advert(level))
    assert tag.values == {"level": 60}
    assert listener.call_count == 2


def test_event_listeners_get_the_event_type(bluetooth: FakeBluetooth) -> None:
    tag = started_tag()
    listener = MagicMock()
    tag.async_on_event("ping", listener)
    bluetooth.deliver(fake_advert(ping=True))
    listener.assert_called_once_with("ping")


def test_unsubscribed_listener_is_not_called(bluetooth: FakeBluetooth) -> None:
    tag = started_tag()
    listener = MagicMock()
    tag.async_on_value("level", listener)()
    bluetooth.deliver(fake_advert())
    listener.assert_not_called()
