"""Unit tests for the tracker building blocks."""

import pytest

from custom_components.ble_beacon_telemetry.tracking import LatchedPress, SmoothedLevel

from ..conftest import PROXY_A, PROXY_B


def feed(level: SmoothedLevel, *readings: float) -> int:
    """Add readings and return how many of them changed the level."""
    return sum(level.add(reading) for reading in readings)


def test_first_reading_sets_the_level() -> None:
    level = SmoothedLevel()
    assert feed(level, 79) == 1
    assert level.level == 79


def test_level_ignores_jitter_and_a_single_dip() -> None:
    level = SmoothedLevel(samples=10, step=5)
    assert feed(level, 79, 80, 78, 35, 81, 77) == 1
    assert level.level == 79


def test_level_follows_a_lasting_drop() -> None:
    level = SmoothedLevel(samples=10, step=5)
    assert feed(level, 79, *[70] * 10) == 2
    assert level.level is not None
    assert abs(level.level - 70) < 5


def test_press_needs_a_change_from_off_to_on() -> None:
    press = LatchedPress()
    assert press.update(PROXY_A, on=False, time=0) is False
    assert press.update(PROXY_A, on=True, time=1) is True
    assert press.update(PROXY_A, on=True, time=10) is False


def test_first_report_of_a_press_is_ignored() -> None:
    """A proxy's first report can be a press that's long over."""
    assert LatchedPress().update(PROXY_A, on=True, time=0) is False


@pytest.mark.parametrize(
    ("seconds_apart", "presses"), [(1, 1), (10, 2)], ids=["same press", "two presses"]
)
def test_press_heard_by_two_proxies(seconds_apart: float, presses: int) -> None:
    press = LatchedPress(dedup_seconds=3)
    press.update(PROXY_A, on=False, time=0)
    press.update(PROXY_B, on=False, time=0)
    results = [
        press.update(PROXY_A, on=True, time=1),
        press.update(PROXY_B, on=True, time=1 + seconds_apart),
    ]
    assert sum(results) == presses
