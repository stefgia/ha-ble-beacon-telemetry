"""Parser tests."""

from custom_components.holyiot_ble.parser import HolyIotReading, parse_payload

from .conftest import ADDRESS, PAYLOAD, PAYLOAD_PRESSED


def test_battery_and_released_button() -> None:
    assert parse_payload(ADDRESS, PAYLOAD) == HolyIotReading(battery=79, pressed=False)


def test_pressed_button() -> None:
    assert parse_payload(ADDRESS, PAYLOAD_PRESSED) == HolyIotReading(battery=79, pressed=True)


def test_second_tag() -> None:
    payload = bytes.fromhex("415ed00d00abcdef0306060000")
    assert parse_payload("D0:0D:00:AB:CD:EF", payload) == HolyIotReading(
        battery=94, pressed=False
    )


def test_other_measurement_has_no_button() -> None:
    temperature = PAYLOAD[:10] + bytes([1, 21, 50])
    assert parse_payload(ADDRESS, temperature) == HolyIotReading(battery=79, pressed=None)


def test_rejects_payload_for_another_mac() -> None:
    assert parse_payload("D0:0D:00:AB:CD:EF", PAYLOAD) is None


def test_rejects_wrong_length() -> None:
    assert parse_payload(ADDRESS, PAYLOAD[:12]) is None
    assert parse_payload(ADDRESS, PAYLOAD + b"\x00") is None


def test_rejects_impossible_battery() -> None:
    assert parse_payload(ADDRESS, PAYLOAD[:1] + bytes([200]) + PAYLOAD[2:]) is None
