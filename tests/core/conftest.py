"""Fixtures for core tests, which use a fake device model."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from .fake_device import FakeDevice


@pytest.fixture
def fake_device() -> Generator[FakeDevice]:
    """Make the fake model the only supported one."""
    device = FakeDevice()
    with patch("custom_components.ble_beacon_telemetry.devices.DEVICES", (device,)):
        yield device
