"""Unit tests for the HolyIOT Beacon model and its tracker, without Home Assistant."""

import pytest

from custom_components.holyiot_ble.device import Update
from custom_components.holyiot_ble.devices.holyiot_beacon import (
    LONG_PRESS,
    HolyIotBeacon,
    HolyIotBeaconTracker,
)

from ...conftest import PROXY_A, PROXY_B, advert
from .samples import beacon_advert, payload

PRESS = ("button", LONG_PRESS)


@pytest.mark.parametrize(
    ("info", "claimed"),
    [
        (beacon_advert(), True),
        (beacon_advert(payload(measurement=1)), False),
        (advert(name="Holy-IOT-S"), False),
    ],
    ids=["button frame", "temperature frame", "no HolyIOT frame"],
)
def test_claims_button_frames_only(info, claimed: bool) -> None:
    assert HolyIotBeacon().matches(info) is claimed


def feed(tracker: HolyIotBeaconTracker, *infos) -> Update:
    """Feed adverts and return everything they changed, merged."""
    total = Update()
    for info in infos:
        update = tracker.update(info)
        total.values.update(update.values)
        total.events.extend(update.events)
    return total


def test_battery_is_smoothed() -> None:
    update = feed(
        HolyIotBeaconTracker(),
        *(beacon_advert(payload(battery=level)) for level in (79, 80, 78, 35, 81)),
    )
    assert update.values == {"battery": 79}


def test_battery_readings_during_a_press_are_skipped() -> None:
    """The coin cell sags while the tag reports a press."""
    tracker = HolyIotBeaconTracker()
    feed(tracker, beacon_advert(payload(battery=79)))
    update = feed(tracker, *[beacon_advert(payload(battery=36, pressed=True))] * 3)
    assert update.values == {}


def test_long_press() -> None:
    update = feed(
        HolyIotBeaconTracker(), beacon_advert(payload()), beacon_advert(payload(pressed=True))
    )
    assert update.events == [PRESS]


def test_flag_seen_first_is_not_a_press() -> None:
    update = feed(HolyIotBeaconTracker(), beacon_advert(payload(pressed=True)))
    assert update.events == []


def test_press_heard_by_two_proxies_counts_once() -> None:
    update = feed(
        HolyIotBeaconTracker(),
        beacon_advert(payload(), source=PROXY_A, at=0),
        beacon_advert(payload(), source=PROXY_B, at=0),
        beacon_advert(payload(pressed=True), source=PROXY_A, at=1),
        beacon_advert(payload(pressed=True), source=PROXY_B, at=2),
    )
    assert update.events == [PRESS]


def test_other_adverts_change_nothing() -> None:
    assert feed(HolyIotBeaconTracker(), advert(name="Holy-IOT-S")) == Update()
