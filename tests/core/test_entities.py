"""Integration tests: the entities and device Home Assistant creates, with a fake model."""

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.holyiot_ble.const import CONF_DEVICE, DOMAIN

from ..conftest import ADDRESS, FakeBluetooth
from .fake_device import fake_advert

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth", "fake_device")

LEVEL = "sensor.fake_tag_1234_battery"
PING = "event.fake_tag_1234_ping"


async def setup_tag(hass: HomeAssistant) -> MockConfigEntry:
    """Add and set up a config entry for a fake tag."""
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, unique_id=ADDRESS, title="Fake Tag 1234", data={CONF_DEVICE: "fake"}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_one_entity_per_description(
    hass: HomeAssistant, bluetooth: FakeBluetooth, entity_registry: er.EntityRegistry
) -> None:
    entry = await setup_tag(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert {entity.unique_id for entity in entities} == {f"{ADDRESS}_level", f"{ADDRESS}_ping"}


async def test_sensor_follows_the_tracker(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_tag(hass)
    bluetooth.deliver(fake_advert(level=42))
    assert hass.states.get(LEVEL).state == "42"


async def test_sensor_restored_after_restart(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    mock_restore_cache_with_extra_data(
        hass, [(State(LEVEL, "81"), {"native_value": 81, "native_unit_of_measurement": None})]
    )
    await setup_tag(hass)
    assert hass.states.get(LEVEL).state == "81"


async def test_event_fires(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_tag(hass)
    assert hass.states.get(PING).state == "unknown"
    bluetooth.deliver(fake_advert(ping=True))
    assert hass.states.get(PING).attributes["event_type"] == "ping"


async def test_device_names_the_model_and_links_by_mac(
    hass: HomeAssistant, bluetooth: FakeBluetooth, device_registry: dr.DeviceRegistry
) -> None:
    other = MockConfigEntry(domain="bermuda")
    other.add_to_hass(hass)
    existing = device_registry.async_get_or_create(
        config_entry_id=other.entry_id,
        connections={(dr.CONNECTION_BLUETOOTH, ADDRESS)},
        identifiers={("bermuda", ADDRESS.lower())},
    )
    entry = await setup_tag(hass)
    [ours] = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert (ours.manufacturer, ours.model, ours.name) == ("Test", "Fake Tag", "Fake Tag 1234")
    linked = device_registry.async_get_devices(connections=ours.connections)
    assert {device.id for device in linked} == {ours.id, existing.id}


async def test_unload_stops_listening(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    entry = await setup_tag(hass)
    assert bluetooth.callbacks
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not bluetooth.callbacks
