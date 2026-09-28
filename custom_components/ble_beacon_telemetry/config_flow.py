"""Config flow for BLE Beacon Telemetry: one entry per beacon, found by Bluetooth discovery or added by MAC."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from . import devices
from .const import CONF_DEVICE, DOMAIN
from .device import Device
from .devices import find_device

_LOGGER = logging.getLogger(__name__)

# The choice in the list of heard beacons that asks for a MAC address instead.
MANUAL = "manual"
MAC_ADDRESS = re.compile(r"[0-9A-F]{2}(:[0-9A-F]{2}){5}")


def beacon_title(device: Device, address: str) -> str:
    """Name a beacon after its model and the last four hex digits of its MAC."""
    return f"{device.name} {address.replace(':', '')[-4:]}"


class BeaconConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a beacon."""

    VERSION = 1

    def __init__(self) -> None:
        """Set up the flow's state."""
        self._discovered: tuple[Device, str] | None = None
        # Beacons offered in the user step: address -> (model, title).
        self._candidates: dict[str, tuple[Device, str]] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a beacon found by Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if (device := find_device(discovery_info)) is None:
            # No broadcast name: it can be personal, and this log goes into pull requests.
            _LOGGER.debug(
                "No supported model for %s: service data %s, manufacturer data %s",
                discovery_info.address,
                {uuid: data.hex() for uuid, data in discovery_info.service_data.items()},
                {mfr: data.hex() for mfr, data in discovery_info.manufacturer_data.items()},
            )
            return self.async_abort(reason="not_supported")
        self._discovered = (device, beacon_title(device, discovery_info.address))
        self.context["title_placeholders"] = {"name": self._discovered[1]}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask before adding a discovered beacon."""
        assert self._discovered is not None
        device, title = self._discovered
        if user_input is not None:
            return self.async_create_entry(title=title, data={CONF_DEVICE: device.id})
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders={"name": title}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick one of the beacons Home Assistant has heard but not yet added, or type one in."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            if address == MANUAL:
                return await self.async_step_manual()
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            device, title = self._candidates[address]
            return self.async_create_entry(title=title, data={CONF_DEVICE: device.id})

        configured = self._async_current_ids(include_ignore=False)
        self._candidates = {
            info.address: (device, beacon_title(device, info.address))
            for info in async_discovered_service_info(self.hass, connectable=False)
            if info.address not in configured and (device := find_device(info)) is not None
        }
        if not self._candidates:
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{title} ({address})"
                            for address, (_, title) in self._candidates.items()
                        }
                        | {MANUAL: "Enter a MAC address"}
                    )
                }
            ),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a beacon by its MAC address, before Home Assistant has read its data."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].upper()
            if MAC_ADDRESS.fullmatch(address):
                await self.async_set_unique_id(address, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                device = devices.get_device(user_input[CONF_DEVICE])
                assert device is not None
                return self.async_create_entry(
                    title=beacon_title(device, address), data={CONF_DEVICE: device.id}
                )
            errors[CONF_ADDRESS] = "invalid_address"
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Required(CONF_DEVICE): vol.In(
                        {device.id: device.name for device in devices.DEVICES}
                    ),
                }
            ),
            errors=errors,
        )
