"""Events, one per EventEntityDescription in the beacon's device model."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import BeaconConfigEntry
from .entity import BeaconEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BeaconConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the beacon's events."""
    beacon = entry.runtime_data
    async_add_entities(BeaconEvent(beacon, description) for description in beacon.device.events)


class BeaconEvent(BeaconEntity, EventEntity):
    """Fires the event types the beacon's tracker reports for this key."""

    async def async_added_to_hass(self) -> None:
        """Follow the beacon's events."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.beacon.async_on_event(self.entity_description.key, self._async_fire)
        )

    @callback
    def _async_fire(self, event_type: str) -> None:
        self._trigger_event(event_type)
        self.async_write_ha_state()
