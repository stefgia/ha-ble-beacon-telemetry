"""The interfaces a supported device implements.

Each device model lives in its own folder under devices/ and provides:

- a Device subclass: what the model is called, how Home Assistant finds it,
  and which entities it has;
- a Tracker subclass: turns one beacon's adverts into sensor values and events.

The rest of the integration (config flow, entities, restore after restart) is
shared and works from these alone.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.event import EventEntityDescription
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.typing import StateType


@dataclass
class Update:
    """What one advert changed."""

    # Sensor key -> latest value. Only include values the advert carried.
    values: dict[str, StateType] = field(default_factory=dict)
    # (event entity key, event type) for each event the advert fired.
    events: list[tuple[str, str]] = field(default_factory=list)


class Tracker(ABC):
    """The state of one beacon, built up from its adverts.

    The integration makes one tracker per beacon and hands it every advert from
    that beacon, from any proxy. Keep whatever history is needed here, for
    example to smooth a reading or to spot the moment a button flag goes on.
    """

    @abstractmethod
    def update(self, service_info: BluetoothServiceInfoBleak) -> Update:
        """Read an advert and return what changed. Return Update() if nothing did."""


class Device(ABC):
    """A supported device model."""

    # Unique, lowercase, the same as the folder name. Stored in config entries,
    # so it must never change once released.
    id: ClassVar[str]
    # The model name shown in Home Assistant, e.g. "HolyIOT Button Tag".
    name: ClassVar[str]
    # The maker shown in Home Assistant, e.g. "HolyIOT".
    manufacturer: ClassVar[str]
    # Advert filters Home Assistant uses to discover the device, with the same
    # keys as the "bluetooth" list in manifest.json. Each one must also be in
    # manifest.json: Home Assistant only reads discovery filters from there.
    discovery: ClassVar[tuple[dict[str, Any], ...]]
    # Whether the useful data only arrives in the scan response. If so, the
    # integration asks proxies on Auto to scan actively for the beacon now and then.
    needs_active_scan: ClassVar[bool] = True
    # The entities each beacon gets. Keys must be unique within the device; they
    # become part of each entity's unique ID, so don't change them once released.
    sensors: ClassVar[tuple[SensorEntityDescription, ...]] = ()
    events: ClassVar[tuple[EventEntityDescription, ...]] = ()

    @abstractmethod
    def matches(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Say whether an advert comes from this model.

        Several models can share a discovery filter, so check the content: the
        advert must carry data this device's tracker can read.
        """

    @abstractmethod
    def create_tracker(self) -> Tracker:
        """Return a new tracker for one beacon."""
