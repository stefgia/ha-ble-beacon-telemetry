"""A minimal device model, so the core can be tested without any real device's quirks.

Its service data is two bytes: a level, and an event flag that fires "ping"
whenever it is 1.
"""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.event import EventEntityDescription
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription

from custom_components.holyiot_ble.device import Device, Tracker, Update

from ..conftest import advert

FAKE_UUID = "0000feed-0000-1000-8000-00805f9b34fb"


def fake_advert(level: int = 50, ping: bool = False, **kwargs) -> BluetoothServiceInfoBleak:
    """An advert from a fake tag."""
    return advert(service_data={FAKE_UUID: bytes([level, ping])}, **kwargs)


class FakeTracker(Tracker):
    """Reports the level as it comes, and a ping for each flagged advert."""

    def update(self, service_info: BluetoothServiceInfoBleak) -> Update:
        """Read an advert and return what changed."""
        data = service_info.service_data[FAKE_UUID]
        update = Update(values={"level": data[0]})
        if data[1]:
            update.events.append(("ping", "ping"))
        return update


class FakeDevice(Device):
    """A made-up model."""

    id = "fake"
    name = "Fake Tag"
    manufacturer = "Test"
    discovery = ({"connectable": False, "service_data_uuid": FAKE_UUID},)
    sensors = (SensorEntityDescription(key="level", device_class=SensorDeviceClass.BATTERY),)
    events = (EventEntityDescription(key="ping", name="Ping", event_types=["ping"]),)

    def matches(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Claim adverts with the fake UUID."""
        return FAKE_UUID in service_info.service_data

    def create_tracker(self) -> Tracker:
        """Return a new tracker for one tag."""
        return FakeTracker()
