"""Follow one tag's adverts and turn them into a battery level and long presses."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from statistics import median

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .parser import HolyIotReading, parse_service_info

# Two proxies can report the same press a moment apart. Presses closer together
# than this count once.
PRESS_DEDUP_SECONDS = 3.0

# Battery readings jump by a few percent between adverts. The reported level is
# the median of the last BATTERY_SAMPLES readings, and it only moves once that
# median is BATTERY_STEP or more away from it.
BATTERY_SAMPLES = 10
BATTERY_STEP = 5

type Listener = Callable[[], None]


class HolyIotTag:
    """The latest state of one HolyIOT tag."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        """Start with nothing known."""
        self.hass = hass
        self.address = address
        self.name = name
        # The smoothed level, not the last reading.
        self.battery: int | None = None
        self._battery_readings: deque[int] = deque(maxlen=BATTERY_SAMPLES)
        self._battery_listeners: list[Listener] = []
        self._press_listeners: list[Listener] = []
        # Each proxy keeps its own copy of the tag's last scan response, so a
        # press is a change from released to pressed as seen by one proxy.
        self._pressed_by_source: dict[str, bool] = {}
        self._last_press: float | None = None

    @callback
    def async_start(self) -> CALLBACK_TYPE:
        """Listen for the tag's adverts; returns the function that stops it.

        ACTIVE mode with the tag's address makes Auto-mode proxies scan actively
        for this tag now and then, which is when its battery and button data
        arrive. Proxies set to Passive never deliver them.
        """
        return async_register_callback(
            self.hass,
            self._async_on_advert,
            BluetoothCallbackMatcher(address=self.address, connectable=False),
            BluetoothScanningMode.ACTIVE,
        )

    @callback
    def async_on_battery(self, listener: Listener) -> CALLBACK_TYPE:
        """Call `listener` when the battery level changes."""
        return _subscribe(self._battery_listeners, listener)

    @callback
    def async_on_press(self, listener: Listener) -> CALLBACK_TYPE:
        """Call `listener` on each long press of the button."""
        return _subscribe(self._press_listeners, listener)

    @callback
    def _async_on_advert(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        if (reading := parse_service_info(service_info)) is None:
            return
        if self._update_battery(reading):
            _notify(self._battery_listeners)
        if reading.pressed is not None and self._is_new_press(
            service_info.source, reading.pressed, service_info.time
        ):
            _notify(self._press_listeners)

    def _update_battery(self, reading: HolyIotReading) -> bool:
        """Take in a reading and say whether the reported level changed."""
        # The coin cell sags while the tag reports a press, so skip those.
        if reading.pressed:
            return False
        self._battery_readings.append(reading.battery)
        level = round(median(self._battery_readings))
        if self.battery is not None and abs(level - self.battery) < BATTERY_STEP:
            return False
        self.battery = level
        return True

    def _is_new_press(self, source: str, pressed: bool, time: float) -> bool:
        """Record what `source` reports and say whether it's a press to announce."""
        was_pressed = self._pressed_by_source.get(source)
        self._pressed_by_source[source] = pressed
        # A proxy's first report can be a press that's long over, so only a
        # change it has seen happen counts.
        if not pressed or was_pressed is not False:
            return False
        if self._last_press is not None and time - self._last_press < PRESS_DEDUP_SECONDS:
            return False
        self._last_press = time
        return True


def _subscribe(listeners: list[Listener], listener: Listener) -> CALLBACK_TYPE:
    listeners.append(listener)
    return lambda: listeners.remove(listener)


def _notify(listeners: list[Listener]) -> None:
    # Copy, so a listener can unsubscribe while being called.
    for listener in list(listeners):
        listener()
