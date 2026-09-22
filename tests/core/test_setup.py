"""Integration tests for setting up and migrating config entries."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.holyiot_ble.const import CONF_DEVICE, DOMAIN

from ..conftest import ADDRESS, FakeBluetooth

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")


async def test_version_1_entry_becomes_a_holyiot_beacon(
    hass: HomeAssistant, bluetooth: FakeBluetooth
) -> None:
    """Version 1 stored no model: it only supported the button tag."""
    entry = MockConfigEntry(domain=DOMAIN, version=1, unique_id=ADDRESS, title="HolyIOT 1234")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.version == 2
    assert entry.data == {CONF_DEVICE: "holyiot_beacon"}
    assert entry.state is ConfigEntryState.LOADED


async def test_unknown_model_fails_setup(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, version=2, unique_id=ADDRESS, data={CONF_DEVICE: "gone"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
