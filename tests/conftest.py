"""Shared fixtures: Bluetooth with no real adapter, and adverts from a tag."""

from __future__ import annotations

import time

import pytest
from bleak.backends.device import BLEDevice
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_get_advertisement_callback,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.holyiot_ble.const import DOMAIN, SERVICE_UUID

ADDRESS = "C0:FF:EE:00:12:34"
PROXY_A = "AA:00:00:00:00:01"
PROXY_B = "AA:00:00:00:00:02"
# 79 % battery, button type, not pressed.
PAYLOAD = bytes.fromhex("414fc0ffee0012340206060000")
PAYLOAD_PRESSED = bytes.fromhex("414fc0ffee0012340206060100")
IBEACON = bytes.fromhex("0215fda50693a4e24fb1afcfc6eb07647825271b4cb9c9")


def service_info(
    payload: bytes | None = PAYLOAD,
    *,
    address: str = ADDRESS,
    source: str = PROXY_A,
    rssi: int = -60,
) -> BluetoothServiceInfoBleak:
    """An advert as an ESPHome proxy passes it on."""
    return BluetoothServiceInfoBleak(
        name="Holy-IOT-S",
        address=address,
        rssi=rssi,
        manufacturer_data={76: IBEACON},
        service_data={} if payload is None else {SERVICE_UUID: payload},
        service_uuids=[],
        source=source,
        device=BLEDevice(address, "Holy-IOT-S", None),
        advertisement=None,
        connectable=False,
        time=time.monotonic(),
        tx_power=None,
    )


def inject(hass: HomeAssistant, info: BluetoothServiceInfoBleak) -> None:
    """Hand an advert to HA's Bluetooth manager as a proxy would."""
    async_get_advertisement_callback(hass)(info)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let HA load custom_components/holyiot_ble in every test."""
    return


@pytest.fixture(autouse=True)
async def bluetooth(hass: HomeAssistant, mock_bluetooth: None) -> None:
    """Set up HA's Bluetooth integration without an adapter."""
    assert await async_setup_component(hass, "bluetooth", {})
    await hass.async_block_till_done()


async def setup_tag(hass: HomeAssistant) -> MockConfigEntry:
    """Add and set up a config entry for the tag."""
    entry = MockConfigEntry(domain=DOMAIN, unique_id=ADDRESS, title="HolyIOT 1234")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
