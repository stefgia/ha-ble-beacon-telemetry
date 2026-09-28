"""Integration tests for setting up config entries."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_beacon_telemetry.const import CONF_DEVICE, DOMAIN

from ..conftest import ADDRESS, FakeBluetooth

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")


async def test_unknown_model_fails_setup(hass: HomeAssistant, bluetooth: FakeBluetooth) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_DEVICE: "gone"}
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR
