"""DEVICE NAME: one line on what it is. See README.md in this folder."""

# Copy this folder to custom_components/ble_beacon_telemetry/devices/<device_id>/ and
# replace every TODO. Keep device-specific code in this folder only.

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory

from ...device import Device, Tracker, Update
from ...tracking import SmoothedLevel
from .parser import SERVICE_UUID, parse_service_info


class MyDevice(Device):  # TODO: name the class after the model
    """TODO: the model, in one line."""

    id = "my_device"  # TODO: the same as the folder name; never change it once released
    name = "Maker Model"  # TODO: the model name shown in Home Assistant
    manufacturer = "Maker"  # TODO: the maker shown in Home Assistant
    # TODO: how Home Assistant finds it. Add the same filter to manifest.json.
    discovery = ({"connectable": False, "service_data_uuid": SERVICE_UUID},)
    # TODO: False if all the data is in the advert itself, not the scan response.
    needs_active_scan = True
    # TODO: one description per value the device reports. Keys are part of the
    # entities' unique IDs, so never change them once released.
    sensors = (
        SensorEntityDescription(
            key="battery",
            device_class=SensorDeviceClass.BATTERY,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    )
    # TODO: EventEntityDescription(...) for buttons and other one-off events.
    events = ()

    def matches(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Claim adverts this tracker can read, and no others.

        Be specific: other models may share the discovery filter.
        """
        return parse_service_info(service_info) is not None

    def create_tracker(self) -> Tracker:
        """Return a new tracker for one beacon."""
        return MyDeviceTracker()


class MyDeviceTracker(Tracker):
    """TODO: what this tracker smooths, filters or detects."""

    def __init__(self) -> None:
        """Start with nothing known."""
        self._battery = SmoothedLevel(samples=10, step=5)

    def update(self, service_info: BluetoothServiceInfoBleak) -> Update:
        """Read an advert and return what changed."""
        update = Update()
        if (reading := parse_service_info(service_info)) is None:
            return update
        if self._battery.add(reading.battery):
            update.values["battery"] = self._battery.level
        return update
