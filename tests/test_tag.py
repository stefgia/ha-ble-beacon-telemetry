"""Entity tests: battery, button presses and the shared device."""

import time

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from .conftest import (
    ADDRESS,
    PAYLOAD,
    PAYLOAD_PRESSED,
    PROXY_A,
    PROXY_B,
    inject,
    service_info,
    setup_tag,
)

BATTERY = "sensor.holyiot_1234_battery"
BUTTON = "event.holyiot_1234_button"


async def test_battery_from_advert(hass: HomeAssistant) -> None:
    await setup_tag(hass)
    inject(hass, service_info())
    await hass.async_block_till_done()
    assert hass.states.get(BATTERY).state == "79"


async def test_advert_already_heard_is_used_at_setup(hass: HomeAssistant) -> None:
    inject(hass, service_info())
    await hass.async_block_till_done()
    await setup_tag(hass)
    assert hass.states.get(BATTERY).state == "79"


async def test_battery_restored_after_restart(hass: HomeAssistant) -> None:
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(BATTERY, "81"),
                {"native_value": 81, "native_unit_of_measurement": "%"},
            )
        ],
    )
    await setup_tag(hass)
    assert hass.states.get(BATTERY).state == "81"


async def test_press_fires_event(hass: HomeAssistant) -> None:
    await setup_tag(hass)
    inject(hass, service_info(PAYLOAD))
    inject(hass, service_info(PAYLOAD_PRESSED))
    await hass.async_block_till_done()
    state = hass.states.get(BUTTON)
    assert state.attributes["event_type"] == "press"


async def test_stale_press_at_setup_is_ignored(hass: HomeAssistant) -> None:
    inject(hass, service_info(PAYLOAD_PRESSED))
    await hass.async_block_till_done()
    await setup_tag(hass)
    assert hass.states.get(BUTTON).state == "unknown"


async def test_two_proxies_report_one_press(hass: HomeAssistant) -> None:
    await setup_tag(hass)
    fired: list[str] = []
    hass.bus.async_listen("state_changed", lambda e: fired.append(e.data["entity_id"]))
    inject(hass, service_info(PAYLOAD, source=PROXY_A))
    await hass.async_block_till_done()
    inject(hass, service_info(PAYLOAD, source=PROXY_B, rssi=-40))
    await hass.async_block_till_done()
    inject(hass, service_info(PAYLOAD_PRESSED, source=PROXY_A, rssi=-40))
    await hass.async_block_till_done()
    inject(hass, service_info(PAYLOAD_PRESSED, source=PROXY_B, rssi=-30))
    await hass.async_block_till_done()
    assert fired.count(BUTTON) == 1


async def test_presses_further_apart_both_count(hass: HomeAssistant) -> None:
    await setup_tag(hass)
    fired: list[str] = []
    hass.bus.async_listen("state_changed", lambda e: fired.append(e.data["entity_id"]))
    start = time.monotonic()
    for offset, payload in ((0, PAYLOAD), (1, PAYLOAD_PRESSED), (2, PAYLOAD), (10, PAYLOAD_PRESSED)):
        info = service_info(payload)
        info.time = start + offset
        inject(hass, info)
        await hass.async_block_till_done()
    assert fired.count(BUTTON) == 2


async def test_linked_to_device_made_by_another_integration(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    other = MockConfigEntry(domain="bermuda")
    other.add_to_hass(hass)
    existing = device_registry.async_get_or_create(
        config_entry_id=other.entry_id,
        connections={(dr.CONNECTION_BLUETOOTH, ADDRESS)},
        identifiers={("bermuda", ADDRESS.lower())},
        name="Holy-IOT-S",
    )
    entry = await setup_tag(hass)
    [ours] = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    linked = device_registry.async_get_devices(connections=ours.connections)
    assert {device.id for device in linked} == {ours.id, existing.id}


async def test_unload(hass: HomeAssistant) -> None:
    entry = await setup_tag(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
