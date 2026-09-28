"""End-to-end tests for a HolyIOT Button Tag in Home Assistant."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_beacon_telemetry.const import CONF_DEVICE, DOMAIN

from ...conftest import ADDRESS, FakeBluetooth
from .samples import button_tag_advert, payload

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")

BATTERY = "sensor.holyiot_button_tag_1234_battery"
BUTTON = "event.holyiot_button_tag_1234_button"


async def setup_beacon(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        title="HolyIOT Button Tag 1234",
        data={CONF_DEVICE: "holyiot_button_tag"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_unique_ids_are_the_address_and_key(
    hass: HomeAssistant, bluetooth: FakeBluetooth, entity_registry: er.EntityRegistry
) -> None:
    """Changing these would orphan the entities of beacons already added."""
    entry = await setup_beacon(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert {entity.unique_id for entity in entities} == {
        f"{ADDRESS}_battery",
        f"{ADDRESS}_button",
    }


async def test_battery_and_long_press(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_beacon(hass)
    bluetooth.deliver(button_tag_advert(payload()))
    bluetooth.deliver(button_tag_advert(payload(pressed=True)))
    assert hass.states.get(BATTERY).state == "79"
    assert hass.states.get(BUTTON).attributes["event_type"] == "long_press"
