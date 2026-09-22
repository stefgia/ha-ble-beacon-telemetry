"""Integration tests for the config flow, with a fake device model."""

from typing import Any
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.holyiot_ble.const import CONF_DEVICE, DOMAIN

from ..conftest import ADDRESS, advert
from .fake_device import fake_advert

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth", "fake_device")

TITLE = "Fake Tag 1234"


async def start_flow(hass: HomeAssistant, source: str, data: Any = None) -> dict[str, Any]:
    """Start a config flow the way discovery or the Add integration dialog would."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}, data=data
    )


def heard(*infos: Any):
    """Make these the adverts Home Assistant has heard."""
    return patch(
        "custom_components.holyiot_ble.config_flow.async_discovered_service_info",
        return_value=list(infos),
    )


async def test_bluetooth_discovery_adds_tag(hass: HomeAssistant) -> None:
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, fake_advert())
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_DEVICE: "fake"}
    assert result["result"].unique_id == ADDRESS


async def test_bluetooth_discovery_of_unsupported_device(hass: HomeAssistant) -> None:
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, advert())
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_bluetooth_discovery_of_configured_tag(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, fake_advert())
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_picks_a_heard_tag(hass: HomeAssistant) -> None:
    with heard(fake_advert()):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_DEVICE: "fake"}


async def test_user_skips_configured_and_unsupported(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    with heard(fake_advert(), advert(address="D0:0D:00:AB:CD:EF")):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"
