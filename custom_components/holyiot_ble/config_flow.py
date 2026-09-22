"""Config flow for HolyIOT BLE: one entry per tag, found by Bluetooth discovery."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import CONF_DEVICE, DOMAIN
from .device import Device
from .devices import find_device

_LOGGER = logging.getLogger(__name__)


def tag_title(device: Device, address: str) -> str:
    """Name a tag after its model and the last four hex digits of its MAC."""
    return f"{device.name} {address.replace(':', '')[-4:]}"


class HolyIotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a HolyIOT tag."""

    VERSION = 2

    def __init__(self) -> None:
        """Set up the flow's state."""
        self._discovered: tuple[Device, str] | None = None
        # Tags offered in the user step: address -> (model, title).
        self._candidates: dict[str, tuple[Device, str]] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a tag found by Bluetooth discovery."""
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
        self._discovered = (device, tag_title(device, discovery_info.address))
        self.context["title_placeholders"] = {"name": self._discovered[1]}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask before adding a discovered tag."""
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
        """Pick one of the tags Home Assistant has heard but not yet added."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            device, title = self._candidates[address]
            return self.async_create_entry(title=title, data={CONF_DEVICE: device.id})

        configured = self._async_current_ids(include_ignore=False)
        self._candidates = {
            info.address: (device, tag_title(device, info.address))
            for info in async_discovered_service_info(self.hass, connectable=False)
            if info.address not in configured and (device := find_device(info)) is not None
        }
        if not self._candidates:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{title} ({address})"
                            for address, (_, title) in self._candidates.items()
                        }
                    )
                }
            ),
        )
