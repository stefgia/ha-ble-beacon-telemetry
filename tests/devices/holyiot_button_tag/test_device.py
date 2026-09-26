"""Unit tests for the HolyIOT Button Tag model and its tracker, without Home Assistant."""

import pytest

from custom_components.ble_beacon_telemetry.device import Update
from custom_components.ble_beacon_telemetry.devices.holyiot_button_tag import (
    LONG_PRESS,
    HolyIotButtonTag,
    HolyIotButtonTagTracker,
)

from ...conftest import PROXY_A, PROXY_B, advert
from .samples import button_tag_advert, payload

PRESS = ("button", LONG_PRESS)


@pytest.mark.parametrize(
    ("info", "claimed"),
    [
        (button_tag_advert(), True),
        (button_tag_advert(payload(measurement=1)), False),
        (advert(name="Holy-IOT-S"), False),
    ],
    ids=["button frame", "temperature frame", "no HolyIOT frame"],
)
def test_claims_button_frames_only(info, claimed: bool) -> None:
    assert HolyIotButtonTag().matches(info) is claimed


def feed(tracker: HolyIotButtonTagTracker, *infos) -> Update:
    """Feed adverts and return everything they changed, merged."""
    total = Update()
    for info in infos:
        update = tracker.update(info)
        total.values.update(update.values)
        total.events.extend(update.events)
    return total


def test_battery_is_smoothed() -> None:
    update = feed(
        HolyIotButtonTagTracker(),
        *(button_tag_advert(payload(battery=level)) for level in (79, 80, 78, 35, 81)),
    )
    assert update.values == {"battery": 79}


def test_battery_readings_during_a_press_are_skipped() -> None:
    """The coin cell sags while the tag reports a press."""
    tracker = HolyIotButtonTagTracker()
    feed(tracker, button_tag_advert(payload(battery=79)))
    update = feed(tracker, *[button_tag_advert(payload(battery=36, pressed=True))] * 3)
    assert update.values == {}


def test_long_press() -> None:
    update = feed(
        HolyIotButtonTagTracker(), button_tag_advert(payload()), button_tag_advert(payload(pressed=True))
    )
    assert update.events == [PRESS]


def test_flag_seen_first_is_not_a_press() -> None:
    update = feed(HolyIotButtonTagTracker(), button_tag_advert(payload(pressed=True)))
    assert update.events == []


def test_press_heard_by_two_proxies_counts_once() -> None:
    update = feed(
        HolyIotButtonTagTracker(),
        button_tag_advert(payload(), source=PROXY_A, at=0),
        button_tag_advert(payload(), source=PROXY_B, at=0),
        button_tag_advert(payload(pressed=True), source=PROXY_A, at=1),
        button_tag_advert(payload(pressed=True), source=PROXY_B, at=2),
    )
    assert update.events == [PRESS]


def test_other_adverts_change_nothing() -> None:
    assert feed(HolyIotButtonTagTracker(), advert(name="Holy-IOT-S")) == Update()
