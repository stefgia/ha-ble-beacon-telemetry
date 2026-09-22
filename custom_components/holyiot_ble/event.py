"""Button event."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HolyIotConfigEntry
from .entity import HolyIotEntity

LONG_PRESS = "long_press"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HolyIotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the tag's button."""
    async_add_entities([HolyIotButtonEvent(entry.runtime_data)])


class HolyIotButtonEvent(HolyIotEntity, EventEntity):
    """Fires `long_press` when the tag's button is held for about 3 seconds.

    The tags don't report short presses.
    """

    _key = "button"
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = [LONG_PRESS]
    _attr_translation_key = "button"

    async def async_added_to_hass(self) -> None:
        """Follow the tag's presses."""
        await super().async_added_to_hass()
        self.async_on_remove(self.tag.async_on_press(self._async_press))

    @callback
    def _async_press(self) -> None:
        self._trigger_event(LONG_PRESS)
        self.async_write_ha_state()
