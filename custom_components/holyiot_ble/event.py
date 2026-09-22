"""Events, one per EventEntityDescription in the tag's device model."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HolyIotConfigEntry
from .entity import HolyIotEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HolyIotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the tag's events."""
    tag = entry.runtime_data
    async_add_entities(HolyIotEvent(tag, description) for description in tag.device.events)


class HolyIotEvent(HolyIotEntity, EventEntity):
    """Fires the event types the tag's tracker reports for this key."""

    async def async_added_to_hass(self) -> None:
        """Follow the tag's events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.tag.async_on_event(self.entity_description.key, self._async_fire)
        )

    @callback
    def _async_fire(self, event_type: str) -> None:
        self._trigger_event(event_type)
        self.async_write_ha_state()
