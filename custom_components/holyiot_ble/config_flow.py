"""Config flow for HolyIOT BLE: one entry per tag, found by Bluetooth discovery."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN
from .parser import parse_service_info


def tag_title(service_info: BluetoothServiceInfoBleak) -> str:
    """Name a tag after the last four hex digits of its MAC, e.g. "HolyIOT 1234"."""
    return f"HolyIOT {service_info.address.replace(':', '')[-4:]}"


class HolyIotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a HolyIOT tag."""

    VERSION = 1

    def __init__(self) -> None:
        """Set up the flow's state."""
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._candidates: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a tag found by Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if parse_service_info(discovery_info) is None:
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        self.context["title_placeholders"] = {"name": tag_title(discovery_info)}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask before adding a discovered tag."""
        assert self._discovery is not None
        title = tag_title(self._discovery)
        if user_input is not None:
            return self.async_create_entry(title=title, data={})
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
            return self.async_create_entry(title=self._candidates[address], data={})

        configured = self._async_current_ids(include_ignore=False)
        for service_info in async_discovered_service_info(self.hass, connectable=False):
            address = service_info.address
            if address in configured or address in self._candidates:
                continue
            if parse_service_info(service_info) is not None:
                self._candidates[address] = tag_title(service_info)
        if not self._candidates:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{title} ({address})"
                            for address, title in self._candidates.items()
                        }
                    )
                }
            ),
        )
