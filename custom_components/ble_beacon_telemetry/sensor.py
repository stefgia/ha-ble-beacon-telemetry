"""Sensors, one per SensorEntityDescription in the beacon's device model."""

from __future__ import annotations

from homeassistant.components.sensor import RestoreSensor
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BeaconConfigEntry
from .entity import BeaconEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BeaconConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the beacon's sensors."""
    beacon = entry.runtime_data
    async_add_entities(BeaconSensor(beacon, description) for description in beacon.device.sensors)


class BeaconSensor(BeaconEntity, RestoreSensor):
    """A value from the beacon's tracker.

    It keeps the last value while the beacon is away rather than going
    unavailable, and restores it after a restart.
    """

    async def async_added_to_hass(self) -> None:
        """Restore the last value, then follow the beacon."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value
        self.async_on_remove(
            self.beacon.async_on_value(self.entity_description.key, self._async_update)
        )

    @callback
    def _async_update(self) -> None:
        self._attr_native_value = self.beacon.values[self.entity_description.key]
        self.async_write_ha_state()
