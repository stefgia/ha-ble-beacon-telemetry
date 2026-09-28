"""Follow one beacon's adverts and pass what its tracker reports on to the entities."""

from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.typing import StateType

from .device import Device

_LOGGER = logging.getLogger(__name__)


class Beacon:
    """One configured beacon: its model, its tracker and its latest values."""

    def __init__(self, hass: HomeAssistant, address: str, name: str, device: Device) -> None:
        """Start with nothing known."""
        self.hass = hass
        self.address = address
        self.name = name
        self.device = device
        self.values: dict[str, StateType] = {}
        self._tracker = device.create_tracker()
        self._value_listeners: dict[str, list[Callable[[], None]]] = {}
        self._event_listeners: dict[str, list[Callable[[str], None]]] = {}

    @callback
    def async_start(self) -> CALLBACK_TYPE:
        """Listen for the beacon's adverts; returns the function that stops it.

        ACTIVE mode with the beacon's address makes Auto-mode proxies scan actively
        for this beacon now and then, which is when scan-response data arrives.
        """
        mode = (
            BluetoothScanningMode.ACTIVE
            if self.device.needs_active_scan
            else BluetoothScanningMode.PASSIVE
        )
        return async_register_callback(
            self.hass,
            self._async_on_advert,
            BluetoothCallbackMatcher(address=self.address, connectable=False),
            mode,
        )

    @callback
    def async_on_value(self, key: str, listener: Callable[[], None]) -> CALLBACK_TYPE:
        """Call `listener` when the value for sensor `key` changes."""
        return _subscribe(self._value_listeners.setdefault(key, []), listener)

    @callback
    def async_on_event(self, key: str, listener: Callable[[str], None]) -> CALLBACK_TYPE:
        """Call `listener` with the event type each time event `key` fires."""
        return _subscribe(self._event_listeners.setdefault(key, []), listener)

    @callback
    def _async_on_advert(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        _LOGGER.debug(
            "%s advert from %s: service data %s, manufacturer data %s",
            self.address,
            service_info.source,
            {uuid: data.hex() for uuid, data in service_info.service_data.items()},
            {mfr: data.hex() for mfr, data in service_info.manufacturer_data.items()},
        )
        update = self._tracker.update(service_info)
        for key, value in update.values.items():
            if self.values.get(key) != value:
                self.values[key] = value
                for listener in list(self._value_listeners.get(key, ())):
                    listener()
        for key, event_type in update.events:
            for listener in list(self._event_listeners.get(key, ())):
                listener(event_type)


def _subscribe[T](listeners: list[T], listener: T) -> CALLBACK_TYPE:
    listeners.append(listener)
    return lambda: listeners.remove(listener)
