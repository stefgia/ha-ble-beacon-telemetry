"""Unit tests for the tag: battery changes and press detection, without Home Assistant."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.bluetooth import BluetoothScanningMode

from custom_components.holyiot_ble.tag import HolyIotTag

from .conftest import ADDRESS, PROXY_A, PROXY_B, TITLE, FakeBluetooth, payload, service_info


@pytest.fixture
def tag(bluetooth: FakeBluetooth) -> HolyIotTag:
    """A tag that is listening for adverts."""
    tag = HolyIotTag(MagicMock(), ADDRESS, TITLE)
    tag.async_start()
    return tag


@pytest.fixture
def battery_updates(tag: HolyIotTag) -> MagicMock:
    """A listener for battery changes."""
    listener = MagicMock()
    tag.async_on_battery(listener)
    return listener


@pytest.fixture
def presses(tag: HolyIotTag) -> MagicMock:
    """A listener for button presses."""
    listener = MagicMock()
    tag.async_on_press(listener)
    return listener


def test_asks_for_active_scans_of_this_tag(bluetooth: FakeBluetooth, tag: HolyIotTag) -> None:
    _, _, matcher, mode = bluetooth.register.call_args.args
    assert matcher == {"address": ADDRESS, "connectable": False}
    assert mode is BluetoothScanningMode.ACTIVE


def test_battery_change_notifies_once(
    tag: HolyIotTag, bluetooth: FakeBluetooth, battery_updates: MagicMock
) -> None:
    bluetooth.deliver(service_info())
    bluetooth.deliver(service_info())
    assert tag.battery == 79
    assert battery_updates.call_count == 1

    bluetooth.deliver(service_info(payload(battery=78)))
    assert tag.battery == 78
    assert battery_updates.call_count == 2


def test_ignores_other_data(
    tag: HolyIotTag, bluetooth: FakeBluetooth, battery_updates: MagicMock
) -> None:
    bluetooth.deliver(service_info(b"\x41\x4f"))
    assert tag.battery is None
    battery_updates.assert_not_called()


def test_press(bluetooth: FakeBluetooth, presses: MagicMock) -> None:
    bluetooth.deliver(service_info(payload()))
    bluetooth.deliver(service_info(payload(pressed=True)))
    assert presses.call_count == 1


def test_first_report_of_a_press_is_ignored(bluetooth: FakeBluetooth, presses: MagicMock) -> None:
    """A proxy's first report can be a press that's long over."""
    bluetooth.deliver(service_info(payload(pressed=True)))
    presses.assert_not_called()


def test_still_pressed_is_not_a_new_press(bluetooth: FakeBluetooth, presses: MagicMock) -> None:
    for pressed in (False, True, True):
        bluetooth.deliver(service_info(payload(pressed=pressed)))
    assert presses.call_count == 1


@pytest.mark.parametrize(
    ("seconds_apart", "expected"), [(1, 1), (10, 2)], ids=["same press", "two presses"]
)
def test_press_heard_by_two_proxies(
    bluetooth: FakeBluetooth, presses: MagicMock, seconds_apart: float, expected: int
) -> None:
    bluetooth.deliver(service_info(payload(), source=PROXY_A, at=0))
    bluetooth.deliver(service_info(payload(), source=PROXY_B, at=0))
    bluetooth.deliver(service_info(payload(pressed=True), source=PROXY_A, at=1))
    bluetooth.deliver(service_info(payload(pressed=True), source=PROXY_B, at=1 + seconds_apart))
    assert presses.call_count == expected


def test_unsubscribed_listener_is_not_called(tag: HolyIotTag, bluetooth: FakeBluetooth) -> None:
    listener = MagicMock()
    tag.async_on_battery(listener)()
    bluetooth.deliver(service_info())
    listener.assert_not_called()
