#!/usr/bin/env python3
"""Talk to Home Assistant while adding a device: find it, watch its adverts, read logs.

Set these first (never write them into a file in the repo):
    HA_URL     your Home Assistant address, e.g. http://homeassistant.local:8123
    HA_TOKEN   a long-lived access token (Profile > Security > Long-lived access tokens)

Commands:
    check                         check the address and token work
    list [--seconds N]            devices Home Assistant hears over Bluetooth
    watch DEVICE... [--seconds N] every change in these devices' adverts, and
                                  the state changes of their entities
    debug on|off                  turn this integration's debug logging on or off
    logs [--grep TEXT]            Home Assistant's log, optionally filtered

MAC addresses never appear in the output. Devices show as "Device 1",
"Device 2" and proxies as "Proxy 1"; `list` saves which label is which MAC in
~/.cache/ha-ble-beacon-telemetry/devices.json, outside the repo, and `watch` takes those
labels. `watch` and `logs` output is safe to paste into a pull request. `list`
output is for you only: it shows the names nearby devices broadcast, which can
be personal (a phone or TV name).

Run it with the repo's test environment: .venv/bin/python docs/adding-a-device/ha_tool.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import ssl
import sys
import time
from pathlib import Path
from typing import Any

import aiohttp

DOMAIN = "ble_beacon_telemetry"
LABELS_FILE = Path.home() / ".cache" / "ha-ble-beacon-telemetry" / "devices.json"
MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")


# --- Redaction -----------------------------------------------------------------


class Labels:
    """Stable labels for MACs: devices are "Device N", proxies "Proxy N"."""

    def __init__(self) -> None:
        """Load the labels saved by earlier runs."""
        try:
            self.by_mac: dict[str, str] = json.loads(LABELS_FILE.read_text())
        except (FileNotFoundError, ValueError):
            self.by_mac = {}

    def save(self) -> None:
        """Keep the labels for the next run."""
        LABELS_FILE.parent.mkdir(parents=True, exist_ok=True)
        LABELS_FILE.write_text(json.dumps(self.by_mac, indent=2))

    def label(self, mac: str, kind: str = "Device") -> str:
        """The label for a MAC, making a new one if needed."""
        mac = mac.upper()
        if mac not in self.by_mac:
            count = sum(label.startswith(kind) for label in self.by_mac.values())
            self.by_mac[mac] = f"{kind} {count + 1}"
        return self.by_mac[mac]

    def mac(self, label_or_mac: str) -> str:
        """The MAC for a label (or a MAC as given)."""
        if MAC.fullmatch(label_or_mac):
            return label_or_mac.upper()
        for mac, label in self.by_mac.items():
            if label.lower() == label_or_mac.lower():
                return mac
        sys.exit(f"Unknown device {label_or_mac!r}. Run `list` first.")

    def redact(self, text: str) -> str:
        """Replace every MAC in free text, and the short MAC suffix in names and entity IDs."""
        for mac, label in self.by_mac.items():
            plain = mac.replace(":", "").lower()
            text = re.sub(re.escape(mac), label, text, flags=re.IGNORECASE)
            text = re.sub(plain, f"<{label} MAC>", text, flags=re.IGNORECASE)
            text = re.sub(rf"(?<=[ _]){plain[-4:]}\b", label.lower().replace(" ", ""), text, flags=re.IGNORECASE)
        return MAC.sub(lambda match: self.label(match.group(), "MAC"), text)

    def payload(self, mac: str, data: bytes) -> str:
        """Bytes as spaced hex, with the device's own MAC shown as a label."""
        hex_bytes = [f"{byte:02x}" for byte in data]
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        label = self.by_mac.get(mac.upper(), "MAC")
        for pattern, name in ((mac_bytes, label), (mac_bytes[::-1], f"{label}, reversed")):
            start = data.find(pattern)
            if start >= 0:
                hex_bytes[start : start + 6] = [f"[{name} MAC: bytes {start}-{start + 5}]"]
                break
        return " ".join(hex_bytes)


# --- Home Assistant connection -------------------------------------------------


def settings() -> tuple[str, str]:
    url, token = os.environ.get("HA_URL"), os.environ.get("HA_TOKEN")
    if not url or not token:
        sys.exit("Set HA_URL and HA_TOKEN first. See the top of this file.")
    return url.rstrip("/"), token


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


async def rest(session: aiohttp.ClientSession, method: str, path: str, body: Any = None) -> Any:
    url, token = settings()
    async with session.request(
        method, f"{url}{path}", json=body, headers={"Authorization": f"Bearer {token}"}, ssl=ssl_context()
    ) as response:
        response.raise_for_status()
        return await (response.json() if "json" in response.content_type else response.text())


class Websocket:
    """A logged-in Home Assistant websocket."""

    def __init__(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        self.ws = ws
        self.next_id = 1

    @classmethod
    async def open(cls, session: aiohttp.ClientSession) -> Websocket:
        url, token = settings()
        ws = await session.ws_connect(
            re.sub(r"^http", "ws", url) + "/api/websocket", ssl=ssl_context(), max_msg_size=0
        )
        await ws.receive_json()
        await ws.send_json({"type": "auth", "access_token": token})
        if (reply := await ws.receive_json())["type"] != "auth_ok":
            sys.exit(f"Home Assistant refused the token: {reply.get('message')}")
        return cls(ws)

    async def send(self, message: dict[str, Any]) -> int:
        message_id = self.next_id
        self.next_id += 1
        await self.ws.send_json({"id": message_id, **message})
        return message_id

    async def call(self, message: dict[str, Any]) -> Any:
        message_id = await self.send(message)
        while True:
            reply = await self.ws.receive_json()
            if reply.get("id") == message_id and reply["type"] == "result":
                if not reply["success"]:
                    sys.exit(f"{message['type']} failed: {reply['error']['message']}")
                return reply["result"]

    async def events(self, seconds: float):
        end = time.monotonic() + seconds
        while (left := end - time.monotonic()) > 0:
            try:
                yield await asyncio.wait_for(self.ws.receive_json(), left)
            except TimeoutError:
                return


def now() -> str:
    return time.strftime("%H:%M:%S")


# --- Commands ------------------------------------------------------------------


async def check(session: aiohttp.ClientSession, args: argparse.Namespace) -> None:
    config = await rest(session, "GET", "/api/config")
    ws = await Websocket.open(session)
    scanners = await ws.call({"type": "config_entries/get", "domain": "bluetooth"})
    print(f"Connected to Home Assistant {config['version']}.")
    print(f"Bluetooth adapters and proxies: {len(scanners)}.")


async def list_devices(session: aiohttp.ClientSession, args: argparse.Namespace) -> None:
    labels = Labels()
    ws = await Websocket.open(session)
    await ws.send({"type": "bluetooth/subscribe_advertisements"})
    heard: dict[str, dict[str, Any]] = {}
    print(f"Listening for {args.seconds:.0f} seconds...", file=sys.stderr)
    async for message in ws.events(args.seconds):
        for advert in (message.get("event") or {}).get("add", []):
            heard[advert["address"]] = advert
    for advert in sorted(heard.values(), key=lambda a: a["rssi"], reverse=True):
        mac = advert["address"]
        label = labels.label(mac)
        labels.label(advert["source"], "Proxy")
        data = [f"service {uuid[4:8]}: {labels.payload(mac, bytes.fromhex(h))}" for uuid, h in advert["service_data"].items()]
        data += [f"manufacturer {int(m):#06x}: {labels.payload(mac, bytes.fromhex(h))}" for m, h in advert["manufacturer_data"].items()]
        name = labels.redact((advert["name"] or "").rstrip("\x00"))
        print(f"{label:10} {advert['rssi']:>4} dBm  {labels.label(advert['source'], 'Proxy'):8} name={name!r}")
        for line in data:
            print(f"{'':10} {line}")
    labels.save()
    print(f"\nLabels saved in {LABELS_FILE}. Use them with `watch`.", file=sys.stderr)


async def watch(session: aiohttp.ClientSession, args: argparse.Namespace) -> None:
    labels = Labels()
    macs = [labels.mac(device) for device in args.devices]
    ws = await Websocket.open(session)
    entities = {
        entry["entity_id"]: f"{labels.label(entry['unique_id'][:17])} {entry['unique_id'][18:]}"
        for entry in await ws.call({"type": "config/entity_registry/list"})
        if entry["platform"] == DOMAIN and entry["unique_id"][:17].upper() in macs
    }
    await ws.send({"type": "bluetooth/subscribe_advertisements"})
    if entities:
        await ws.send({"type": "subscribe_trigger", "trigger": {"platform": "state", "entity_id": list(entities)}})
    print(f"Watching {', '.join(labels.label(mac) for mac in macs)} for {args.seconds:.0f} seconds.", file=sys.stderr)
    last: dict[tuple[str, str], bytes] = {}
    async for message in ws.events(args.seconds):
        event = message.get("event") or {}
        for advert in event.get("add", []):
            mac = advert["address"].upper()
            if mac not in macs:
                continue
            fields = [(f"service {u[4:8]}", h) for u, h in advert["service_data"].items()]
            fields += [(f"manufacturer {int(m):#06x}", h) for m, h in advert["manufacturer_data"].items()]
            for name, hex_data in fields:
                data = bytes.fromhex(hex_data)
                previous = last.get((mac, name))
                if previous == data:
                    continue
                last[(mac, name)] = data
                changes = ""
                if previous is not None and len(previous) == len(data):
                    changes = "  changed: " + ", ".join(
                        f"byte {i} {a:02x}->{b:02x}" for i, (a, b) in enumerate(zip(previous, data)) if a != b
                    )
                print(
                    f"{now()} {labels.label(mac)} via {labels.label(advert['source'], 'Proxy')} "
                    f"{advert['rssi']} dBm  {name}: {labels.payload(mac, data)}{changes}",
                    flush=True,
                )
        if trigger := (event.get("variables") or {}).get("trigger"):
            state = trigger["to_state"] or {}
            value = state.get("attributes", {}).get("event_type") or state.get("state")
            print(f"{now()} ENTITY {entities[trigger['entity_id']]} -> {value}", flush=True)
    labels.save()


async def debug(session: aiohttp.ClientSession, args: argparse.Namespace) -> None:
    level = "debug" if args.state == "on" else "warning"
    await rest(session, "POST", "/api/services/logger/set_level", {f"custom_components.{DOMAIN}": level})
    print(f"Debug logging for {DOMAIN} is {args.state}.")


async def logs(session: aiohttp.ClientSession, args: argparse.Namespace) -> None:
    labels = Labels()
    text = await rest(session, "GET", "/api/error_log")
    for line in text.splitlines():
        if args.grep is None or args.grep.lower() in line.lower():
            print(labels.redact(line))
    labels.save()


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check").set_defaults(run=check)
    listing = commands.add_parser("list")
    listing.add_argument("--seconds", type=float, default=30)
    listing.set_defaults(run=list_devices)
    watching = commands.add_parser("watch")
    watching.add_argument("devices", nargs="+", help='labels from `list`, e.g. "Device 1"')
    watching.add_argument("--seconds", type=float, default=300)
    watching.set_defaults(run=watch)
    debugging = commands.add_parser("debug")
    debugging.add_argument("state", choices=["on", "off"])
    debugging.set_defaults(run=debug)
    logging_ = commands.add_parser("logs")
    logging_.add_argument("--grep")
    logging_.set_defaults(run=logs)
    args = parser.parse_args()
    async with aiohttp.ClientSession() as session:
        await args.run(session, args)


if __name__ == "__main__":
    asyncio.run(main())
