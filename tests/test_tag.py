"""Unit tests for the tag: battery smoothing and press detection, without Home Assistant."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.bluetooth import BluetoothScanningMode

from custom_components.holyiot_ble.tag import BATTERY_SAMPLES, BATTERY_STEP, HolyIotTag

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


def test_first_reading_sets_the_level(
    tag: HolyIotTag, bluetooth: FakeBluetooth, battery_updates: MagicMock
) -> None:
    bluetooth.deliver(service_info(payload(battery=79)))
    assert tag.battery == 79
    battery_updates.assert_called_once()


def test_level_ignores_jitter_and_a_single_dip(
    tag: HolyIotTag, bluetooth: FakeBluetooth, battery_updates: MagicMock
) -> None:
    for level in (79, 80, 78, 35, 81, 77):
        bluetooth.deliver(service_info(payload(battery=level)))
    assert tag.battery == 79
    battery_updates.assert_called_once()


def test_readings_during_a_press_are_skipped(
    tag: HolyIotTag, bluetooth: FakeBluetooth
) -> None:
    """The coin cell sags while the tag reports a press."""
    bluetooth.deliver(service_info(payload(battery=79)))
    for _ in range(3):
        bluetooth.deliver(service_info(payload(battery=36, pressed=True)))
    assert tag.battery == 79


def test_level_follows_a_lasting_drop(
    tag: HolyIotTag, bluetooth: FakeBluetooth, battery_updates: MagicMock
) -> None:
    bluetooth.deliver(service_info(payload(battery=79)))
    for _ in range(BATTERY_SAMPLES):
        bluetooth.deliver(service_info(payload(battery=70)))
    assert tag.battery is not None
    assert abs(tag.battery - 70) < BATTERY_STEP
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
