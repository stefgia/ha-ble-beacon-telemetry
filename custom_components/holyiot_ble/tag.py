"""Follow one tag's adverts and turn them into a battery level and button presses."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .parser import parse_service_info

# Two proxies can report the same press a moment apart. Presses closer together
# than this count once.
PRESS_DEDUP_SECONDS = 3.0


class HolyIotTag:
    """The latest state of one HolyIOT tag."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        """Start with nothing known."""
        self.hass = hass
        self.address = address
        self.name = name
        self.battery: int | None = None
        self._listeners: list[Callable[[], None]] = []
        self._press_listeners: list[Callable[[], None]] = []
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
    def async_add_listener(self, update: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `update` when the battery level changes."""
        self._listeners.append(update)
        return lambda: self._listeners.remove(update)

    @callback
    def async_add_press_listener(self, press: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `press` on each button press."""
        self._press_listeners.append(press)
        return lambda: self._press_listeners.remove(press)

    @callback
    def _async_on_advert(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        reading = parse_service_info(service_info)
        if reading is None:
            return
        if reading.battery != self.battery:
            self.battery = reading.battery
            for update in list(self._listeners):
                update()
        if reading.pressed is None:
            return
        was_pressed = self._pressed_by_source.get(service_info.source)
        self._pressed_by_source[service_info.source] = reading.pressed
        # A proxy's first report can be a press that's long over, so only a
        # change it has seen happen counts.
        if not reading.pressed or was_pressed is not False:
            return
        if (
            self._last_press is not None
            and service_info.time - self._last_press < PRESS_DEDUP_SECONDS
        ):
            return
        self._last_press = service_info.time
        for press in list(self._press_listeners):
            press()
