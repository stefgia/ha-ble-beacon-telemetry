"""HolyIOT Button Tag: the nRF52810 button tag. See README.md in this folder."""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.event import EventDeviceClass, EventEntityDescription
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory

from ...device import Device, Tracker, Update
from ...tracking import LatchedPress, SmoothedLevel
from .parser import SERVICE_UUID, parse_service_info

LONG_PRESS = "long_press"


class HolyIotButtonTag(Device):
    """The HolyIOT nRF52810 button tag."""

    id = "holyiot_button_tag"
    name = "HolyIOT Button Tag"
    manufacturer = "HolyIOT"
    discovery = ({"connectable": False, "service_data_uuid": SERVICE_UUID},)
    sensors = (
        SensorEntityDescription(
            key="battery",
            device_class=SensorDeviceClass.BATTERY,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    )
    events = (
        EventEntityDescription(
            key="button",
            translation_key="button",
            device_class=EventDeviceClass.BUTTON,
            event_types=[LONG_PRESS],
        ),
    )

    def matches(self, service_info: BluetoothServiceInfoBleak) -> bool:
        """Claim tags whose HolyIOT frame reports a button.

        Other HolyIOT models send the same frame with a sensor reading instead,
        and are left for their own device.
        """
        reading = parse_service_info(service_info)
        return reading is not None and reading.pressed is not None

    def create_tracker(self) -> Tracker:
        """Return a new tracker for one tag."""
        return HolyIotButtonTagTracker()


class HolyIotButtonTagTracker(Tracker):
    """Smooths the battery level and turns the button flag into long presses."""

    def __init__(self) -> None:
        """Start with nothing known."""
        self._battery = SmoothedLevel(samples=10, step=5)
        self._button = LatchedPress(dedup_seconds=3.0)

    def update(self, service_info: BluetoothServiceInfoBleak) -> Update:
        """Read an advert and return what changed."""
        update = Update()
        if (reading := parse_service_info(service_info)) is None:
            return update
        # The coin cell sags while the tag reports a press, so skip those readings.
        if not reading.pressed and self._battery.add(reading.battery):
            update.values["battery"] = self._battery.level
        if reading.pressed is not None and self._button.update(
            service_info.source, reading.pressed, service_info.time
        ):
            update.events.append(("button", LONG_PRESS))
        return update
