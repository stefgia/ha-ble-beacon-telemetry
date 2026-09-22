"""Integration tests for the config flow."""

from typing import Any
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.holyiot_ble.const import DOMAIN

from .conftest import ADDRESS, TITLE, service_info

pytestmark = pytest.mark.usefixtures("enable_custom_integrations", "mock_bluetooth")


async def start_flow(hass: HomeAssistant, source: str, data: Any = None) -> dict[str, Any]:
    """Start a config flow the way discovery or the Add integration dialog would."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": source}, data=data
    )


async def test_bluetooth_discovery_adds_tag(hass: HomeAssistant) -> None:
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, service_info())
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["result"].unique_id == ADDRESS


async def test_bluetooth_discovery_ignores_other_format(hass: HomeAssistant) -> None:
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, service_info(b"\x41\x4f"))
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


async def test_bluetooth_discovery_of_configured_tag(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, service_info())
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


def heard(*infos: Any):
    """Make these the adverts Home Assistant has heard."""
    return patch(
        "custom_components.holyiot_ble.config_flow.async_discovered_service_info",
        return_value=list(infos),
    )


async def test_user_skips_configured_and_other_devices(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    with heard(service_info(), service_info(b"\x41\x4f")):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_picks_a_heard_tag(hass: HomeAssistant) -> None:
    with heard(service_info()):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE


async def test_user_with_nothing_heard(hass: HomeAssistant) -> None:
    with heard():
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"
