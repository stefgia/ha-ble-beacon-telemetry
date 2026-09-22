"""Sensors, one per SensorEntityDescription in the tag's device model."""

from __future__ import annotations

from homeassistant.components.sensor import RestoreSensor
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HolyIotConfigEntry
from .entity import HolyIotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HolyIotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the tag's sensors."""
    tag = entry.runtime_data
    async_add_entities(HolyIotSensor(tag, description) for description in tag.device.sensors)


class HolyIotSensor(HolyIotEntity, RestoreSensor):
    """A value from the tag's tracker.

    It keeps the last value while the tag is away rather than going
    unavailable, and restores it after a restart.
    """

    async def async_added_to_hass(self) -> None:
        """Restore the last value, then follow the tag."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value
        self.async_on_remove(
            self.tag.async_on_value(self.entity_description.key, self._async_update)
        )

    @callback
    def _async_update(self) -> None:
        self._attr_native_value = self.tag.values[self.entity_description.key]
        self.async_write_ha_state()
