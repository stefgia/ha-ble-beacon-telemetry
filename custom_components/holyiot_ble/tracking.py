"""Building blocks for trackers: readings that jitter, and buttons that latch.

These aren't tied to one model. A tracker can use any of them.
"""

from __future__ import annotations

from collections import deque
from statistics import median


class SmoothedLevel:
    """A level, such as battery percent, from readings that jump around.

    The level is the median of the last `samples` readings, and it only moves
    once that median is `step` or more away from it, so the entity doesn't
    change state on every advert.
    """

    def __init__(self, samples: int = 10, step: int = 5) -> None:
        """Start with no readings."""
        self.step = step
        self.level: int | None = None
        self._readings: deque[float] = deque(maxlen=samples)

    def add(self, reading: float) -> bool:
        """Take in a reading and say whether the level changed."""
        self._readings.append(reading)
        level = round(median(self._readings))
        if self.level is not None and abs(level - self.level) < self.step:
            return False
        self.level = level
        return True


class LatchedPress:
    """Presses from a flag the tag holds on for a while after each press.

    Each proxy keeps its own copy of a tag's last scan response, so a press is
    a change from off to on as seen by one proxy. A proxy's first report can be
    a press that's long over, so it doesn't count. Two proxies can report the
    same press a moment apart, so presses closer than `dedup_seconds` count once.
    """

    def __init__(self, dedup_seconds: float = 3.0) -> None:
        """Start with no flags seen."""
        self.dedup_seconds = dedup_seconds
        self._on_by_source: dict[str, bool] = {}
        self._last_press: float | None = None

    def update(self, source: str, on: bool, time: float) -> bool:
        """Record the flag as `source` reports it and say whether it's a new press."""
        was_on = self._on_by_source.get(source)
        self._on_by_source[source] = on
        if not on or was_on is not False:
            return False
        if self._last_press is not None and time - self._last_press < self.dedup_seconds:
            return False
        self._last_press = time
        return True
