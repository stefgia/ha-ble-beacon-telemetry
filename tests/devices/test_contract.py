"""Checks every registered device must pass. A new device gets them for free.

Each device needs, next to its code in custom_components/holyiot_ble/devices/<id>/:
    README.md
and in tests/devices/<id>/:
    samples.py with ADVERTS, a list of real adverts (MACs replaced) it claims.
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
from homeassistant.helpers.entity import EntityDescription

from custom_components.holyiot_ble.device import Device, Update
from custom_components.holyiot_ble.devices import DEVICES

from ..conftest import TEST_ADDRESSES

INTEGRATION = Path(__file__).parents[2] / "custom_components" / "holyiot_ble"
MANIFEST = json.loads((INTEGRATION / "manifest.json").read_text())
# The names must be in both: strings.json is the source, translations/en.json
# is what Home Assistant loads for English.
NAME_FILES = {
    path: json.loads((INTEGRATION / path).read_text())
    for path in ("strings.json", "translations/en.json")
}
MAC = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", re.IGNORECASE)

pytestmark = pytest.mark.parametrize("device", DEVICES, ids=[device.id for device in DEVICES])


def samples(device: Device) -> list:
    return importlib.import_module(f"tests.devices.{device.id}.samples").ADVERTS


def descriptions(device: Device) -> list[tuple[str, EntityDescription]]:
    return [("sensor", d) for d in device.sensors] + [("event", d) for d in device.events]


def test_id_is_its_folder_name(device: Device) -> None:
    assert re.fullmatch(r"[a-z0-9_]+", device.id)
    assert (INTEGRATION / "devices" / device.id).is_dir()


def test_has_a_readme(device: Device) -> None:
    readme = INTEGRATION / "devices" / device.id / "README.md"
    assert readme.is_file()
    assert readme.read_text().startswith(f"# {device.name}\n")


def test_discovery_filters_are_in_the_manifest(device: Device) -> None:
    """Home Assistant only reads discovery filters from manifest.json."""
    assert device.discovery
    for matcher in device.discovery:
        assert matcher in MANIFEST["bluetooth"]


def test_entity_keys_are_unique(device: Device) -> None:
    keys = [description.key for _, description in descriptions(device)]
    assert keys
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("path", NAME_FILES)
def test_every_entity_has_a_name(device: Device, path: str) -> None:
    """A name comes from the name files, the description's name, or its device class."""
    for platform, description in descriptions(device):
        if description.translation_key:
            assert description.translation_key in NAME_FILES[path]["entity"][platform]
        else:
            assert description.name or description.device_class, description.key


@pytest.mark.parametrize("path", NAME_FILES)
def test_every_event_type_has_a_name(device: Device, path: str) -> None:
    for description in device.events:
        if description.translation_key is None:
            continue
        entity = NAME_FILES[path]["entity"]["event"][description.translation_key]
        names = entity["state_attributes"]["event_type"]["state"]
        for event_type in description.event_types:
            assert event_type in names


def test_samples_are_claimed_and_readable(device: Device) -> None:
    adverts = samples(device)
    assert adverts
    tracker = device.create_tracker()
    keys = {description.key for _, description in descriptions(device)}
    for info in adverts:
        assert device.matches(info)
        update = tracker.update(info)
        assert isinstance(update, Update)
        assert set(update.values) <= keys
        assert {key for key, _ in update.events} <= keys


def test_samples_use_test_macs_only(device: Device) -> None:
    """Samples come from real devices; their MACs must be replaced with test MACs.

    If the payload repeats the MAC, as HolyIOT frames do, replace it there too.
    """
    for info in samples(device):
        assert info.address in TEST_ADDRESSES


def test_readme_contains_no_real_macs(device: Device) -> None:
    readme = (INTEGRATION / "devices" / device.id / "README.md").read_text()
    for mac in MAC.findall(readme):
        assert mac.upper() in TEST_ADDRESSES, mac
