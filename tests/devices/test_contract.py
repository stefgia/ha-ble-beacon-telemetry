"""Checks every registered device must pass. A new device gets them for free.

Each device needs, next to its code in custom_components/ble_beacon_telemetry/devices/<id>/:
    README.md, also linked from the main README's "Supported devices" table
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

from custom_components.ble_beacon_telemetry.device import Device, Update
from custom_components.ble_beacon_telemetry.devices import DEVICES

from ..conftest import TEST_ADDRESSES

ROOT = Path(__file__).parents[2]
INTEGRATION = ROOT / "custom_components" / "ble_beacon_telemetry"
MANIFEST = json.loads((INTEGRATION / "manifest.json").read_text())
# The names must be in both: strings.json is the source, translations/en.json
# is what Home Assistant loads for English.
NAME_FILES = {
    path: json.loads((INTEGRATION / path).read_text())
    for path in ("strings.json", "translations/en.json")
}
# Text from docs/adding-a-device/template that must be replaced before merging.
TEMPLATE_LEFTOVERS = ("TODO", "my_device", "MyDevice", "DEVICE NAME", "Maker Model")
MAC = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", re.IGNORECASE)

pytestmark = pytest.mark.parametrize("device", DEVICES, ids=[device.id for device in DEVICES])


def samples(device: Device) -> list:
    return importlib.import_module(f"tests.devices.{device.id}.samples").ADVERTS


def device_files(device: Device) -> list[Path]:
    folders = (INTEGRATION / "devices" / device.id, ROOT / "tests" / "devices" / device.id)
    return [
        path
        for folder in folders
        for path in sorted(folder.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    ]


def descriptions(device: Device) -> list[tuple[str, EntityDescription]]:
    return [("sensor", d) for d in device.sensors] + [("event", d) for d in device.events]


def test_id_is_its_folder_name(device: Device) -> None:
    assert re.fullmatch(r"[a-z0-9_]+", device.id)
    assert (INTEGRATION / "devices" / device.id).is_dir()


def test_names_its_manufacturer(device: Device) -> None:
    """Models come from many makers, so there's no default to inherit."""
    assert vars(type(device)).get("manufacturer"), "set manufacturer on the device class"


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


def test_is_listed_in_the_main_readme(device: Device) -> None:
    readme = (ROOT / "README.md").read_text()
    assert f"devices/{device.id}/README.md" in readme, "add a row to Supported devices"


def test_claims_no_other_devices_samples(device: Device) -> None:
    """Devices can share a discovery filter, so each must leave the others' adverts alone."""
    for other in DEVICES:
        if other is device:
            continue
        for info in samples(other):
            assert not device.matches(info), f"{device.id} claims a {other.id} sample"


def test_has_no_template_leftovers(device: Device) -> None:
    for path in device_files(device):
        text = path.read_text()
        for leftover in TEMPLATE_LEFTOVERS:
            assert leftover not in text, f"{path.relative_to(ROOT)} still has {leftover!r}"
