"""Integration tests for the config flow, with a fake device model."""

from typing import Any
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ble_beacon_telemetry.config_flow import MANUAL
from custom_components.ble_beacon_telemetry.const import CONF_DEVICE, DOMAIN

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
        "custom_components.ble_beacon_telemetry.config_flow.async_discovered_service_info",
        return_value=list(infos),
    )


async def test_bluetooth_discovery_adds_beacon(hass: HomeAssistant) -> None:
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


async def test_bluetooth_discovery_of_configured_beacon(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    result = await start_flow(hass, config_entries.SOURCE_BLUETOOTH, fake_advert())
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_picks_a_heard_beacon(hass: HomeAssistant) -> None:
    with heard(fake_advert()):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_DEVICE: "fake"}


async def test_user_can_type_an_address_instead_of_picking_a_heard_beacon(
    hass: HomeAssistant,
) -> None:
    with heard(fake_advert()):
        result = await start_flow(hass, config_entries.SOURCE_USER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: MANUAL}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"


async def test_user_asks_for_the_address_when_no_new_beacon_is_heard(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)
    with heard(fake_advert(), advert(address="D0:0D:00:AB:CD:EF")):
        result = await start_flow(hass, config_entries.SOURCE_USER)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"


async def enter_address(hass: HomeAssistant, address: str) -> dict[str, Any]:
    """Open the manual step, with nothing heard, and submit this address for the fake model."""
    with heard():
        result = await start_flow(hass, config_entries.SOURCE_USER)
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: address, CONF_DEVICE: "fake"}
    )


async def test_user_adds_a_beacon_by_its_address(hass: HomeAssistant) -> None:
    result = await enter_address(hass, ADDRESS.lower())

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {CONF_DEVICE: "fake"}
    assert result["result"].unique_id == ADDRESS


async def test_user_cannot_add_a_configured_beacon_by_its_address(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS).add_to_hass(hass)

    result = await enter_address(hass, ADDRESS)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize("address", ["C0:FF:EE:00:12", "C0:FF:EE:00:12:3G", "C0FFEE001234", "tag"])
async def test_user_is_asked_again_for_an_address_that_is_not_a_mac(
    hass: HomeAssistant, address: str
) -> None:
    result = await enter_address(hass, address)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert result["errors"] == {CONF_ADDRESS: "invalid_address"}
