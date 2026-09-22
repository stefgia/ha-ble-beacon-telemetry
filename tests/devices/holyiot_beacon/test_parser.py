"""Parser tests."""

import pytest

from custom_components.holyiot_ble.devices.holyiot_beacon.parser import (
    HolyIotReading,
    parse_payload,
)

from ...conftest import ADDRESS, TEST_ADDRESSES
from .samples import PAYLOAD, payload

OTHER_ADDRESS = TEST_ADDRESSES[1]


@pytest.mark.parametrize(
    ("address", "data", "expected"),
    [
        (ADDRESS, PAYLOAD, HolyIotReading(battery=79, pressed=False)),
        (ADDRESS, payload(pressed=True), HolyIotReading(battery=79, pressed=True)),
        (
            OTHER_ADDRESS,
            bytes.fromhex("415ed00d00abcdef0306060000"),
            HolyIotReading(battery=94, pressed=False),
        ),
        # A temperature frame still carries the battery, but no button.
        (ADDRESS, payload(measurement=1), HolyIotReading(battery=79, pressed=None)),
    ],
    ids=["released", "pressed", "other tag", "not a button"],
)
def test_reads(address: str, data: bytes, expected: HolyIotReading) -> None:
    assert parse_payload(address, data) == expected


@pytest.mark.parametrize(
    ("address", "data"),
    [
        (OTHER_ADDRESS, PAYLOAD),
        (ADDRESS, PAYLOAD[:12]),
        (ADDRESS, PAYLOAD + b"\x00"),
        (ADDRESS, payload(battery=200)),
    ],
    ids=["another tag's MAC", "too short", "too long", "battery over 100"],
)
def test_rejects(address: str, data: bytes) -> None:
    assert parse_payload(address, data) is None
