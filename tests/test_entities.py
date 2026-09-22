"""Integration tests: the entities and device Home Assistant creates for a tag."""

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.holyiot_ble.const import DOMAIN

from .conftest import ADDRESS, TITLE, FakeBluetooth, payload, service_info

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")

BATTERY = "sensor.holyiot_1234_battery"
BUTTON = "event.holyiot_1234_button"


async def setup_tag(hass: HomeAssistant) -> MockConfigEntry:
    """Add and set up a config entry for the tag."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS, title=TITLE)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_battery_sensor(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_tag(hass)
    bluetooth.deliver(service_info())
    assert hass.states.get(BATTERY).state == "79"


async def test_battery_restored_after_restart(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    mock_restore_cache_with_extra_data(
        hass,
        [(State(BATTERY, "81"), {"native_value": 81, "native_unit_of_measurement": "%"})],
    )
    await setup_tag(hass)
    assert hass.states.get(BATTERY).state == "81"


async def test_button_event(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_tag(hass)
    assert hass.states.get(BUTTON).state == "unknown"
    bluetooth.deliver(service_info(payload()))
    bluetooth.deliver(service_info(payload(pressed=True)))
    assert hass.states.get(BUTTON).attributes["event_type"] == "long_press"


async def test_linked_to_device_made_by_another_integration(
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
    linked = device_registry.async_get_devices(connections=ours.connections)
    assert {device.id for device in linked} == {ours.id, existing.id}


async def test_unload_stops_listening(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    entry = await setup_tag(hass)
    assert bluetooth.callbacks
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not bluetooth.callbacks
