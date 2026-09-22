"""Battery sensor."""

from __future__ import annotations

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HolyIotConfigEntry
from .entity import HolyIotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HolyIotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the tag's battery sensor."""
    async_add_entities([HolyIotBatterySensor(entry.runtime_data)])


class HolyIotBatterySensor(HolyIotEntity, RestoreSensor):
    """Battery level from the tag's last scan response.

    It keeps the last level while the tag is away rather than going
    unavailable: the battery hasn't changed just because nobody can hear it.
    """

    _key = "battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    async def async_added_to_hass(self) -> None:
        """Restore the last level, then follow the tag."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value
        self.async_on_remove(self.tag.async_on_battery(self._async_update))

    @callback
    def _async_update(self) -> None:
        self._attr_native_value = self.tag.battery
        self.async_write_ha_state()
