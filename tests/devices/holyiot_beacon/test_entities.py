"""End-to-end tests for a HolyIOT Beacon in Home Assistant."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.holyiot_ble.const import CONF_DEVICE, DOMAIN

from ...conftest import ADDRESS, FakeBluetooth
from .samples import beacon_advert, payload

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")

BATTERY = "sensor.holyiot_beacon_1234_battery"
BUTTON = "event.holyiot_beacon_1234_button"


async def setup_tag(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        unique_id=ADDRESS,
        title="HolyIOT Beacon 1234",
        data={CONF_DEVICE: "holyiot_beacon"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_unique_ids_are_unchanged_since_version_1(
    hass: HomeAssistant, bluetooth: FakeBluetooth, entity_registry: er.EntityRegistry
) -> None:
    """Changing these would orphan the entities of tags added before."""
    entry = await setup_tag(hass)
    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert {entity.unique_id for entity in entities} == {
        f"{ADDRESS}_battery",
        f"{ADDRESS}_button",
    }


async def test_battery_and_long_press(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    await setup_tag(hass)
    bluetooth.deliver(beacon_advert(payload()))
    bluetooth.deliver(beacon_advert(payload(pressed=True)))
    assert hass.states.get(BATTERY).state == "79"
    assert hass.states.get(BUTTON).attributes["event_type"] == "long_press"
