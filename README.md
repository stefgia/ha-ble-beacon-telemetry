# BLE Beacon Telemetry

BLE Beacon Telemetry is a Home Assistant integration for Bluetooth beacons. It reads what a beacon broadcasts about itself, such as its battery level or a button press, and turns it into sensors and events you can use in automations.

It doesn't track where a beacon is. Use it alongside the integration that does, such as Bermuda or Home Assistant's iBeacon Tracker, which give a beacon's location but not its battery or buttons.

It works with the Bluetooth adapters and ESPHome Bluetooth proxies you already have in Home Assistant. You don't need custom proxy firmware.

## Supported devices

| Device | Entities | Details |
| --- | --- | --- |
| HolyIOT Button Tag (nRF52810) | Battery, Button (long press) | [devices/holyiot_button_tag](custom_components/ble_beacon_telemetry/devices/holyiot_button_tag/README.md) |

Each device's page describes what it reports, how it behaves and what it was tested with. To add support for another device, see [Supporting a new device](#supporting-a-new-device).

If Home Assistant already has an integration that reads your device, such as BTHome or Xiaomi BLE, use that one. This integration is for beacons whose data nothing else reads.

## Requirements

- Home Assistant 2026.9.0 or newer.
- A Bluetooth adapter or ESPHome Bluetooth proxy in range of the beacon. Most beacons need it set to Active or Auto scanning (see [Scanning modes](#scanning-modes)).

## Installation

1. In HACS, open the menu in the top right and choose **Custom repositories**.
2. Add `https://github.com/stefgia/ha-ble-beacon-telemetry` with the type **Integration**.
3. Search HACS for **BLE Beacon Telemetry**, download it and restart Home Assistant.

Without HACS, copy the integration into your config folder and restart Home Assistant:

```bash
scripts/deploy.sh /path/to/homeassistant/config
```

## Setting up a beacon

Home Assistant finds beacons by itself and offers them under **Settings > Devices & services**. Select **Add** on a discovered beacon to set it up.

To add one by hand, go to **Settings > Devices & services > Add integration**, choose **BLE Beacon Telemetry** and pick the beacon from the list. A new beacon can take a few minutes to appear on Auto scanning.

## Using it

Each beacon becomes a device with the entities its [device page](#supported-devices) lists. Sensors keep their last value while the beacon is out of range, and after a restart.

Events, such as a button press, show up as an event entity. To run something when one fires, use the entity's state as an automation trigger:

```yaml
triggers:
  - trigger: state
    entity_id: event.holyiot_button_tag_1234_button
actions:
  - action: light.toggle
    target:
      entity_id: light.hallway
```

If another integration tracks the same beacon, such as Bermuda, its device shows up as a linked device.

## Scanning modes

Many beacons send their data only in the scan response, which a Bluetooth adapter or proxy hears only while it scans actively. Its scanning mode decides how much of that data reaches Home Assistant:

| Mode | Sensors | Events |
| --- | --- | --- |
| Active | Always current | Every event |
| Auto (the default for ESPHome proxies) | Update every few minutes | Only events during a short active window, so most are missed |
| Passive | Never | Never |

On Auto, the integration asks the proxy to scan actively for 10 seconds every 5 minutes for each beacon. That's enough for slow sensors such as a battery level. If you use a beacon's events, set at least one proxy near the beacon to Active. For an ESPHome proxy, the scanning mode is in the ESPHome integration's options. Each device page says whether it needs active scanning.

## Uninstalling

Remove the beacons first, then the integration. Removing the integration first leaves its beacons behind as broken entries.

1. Delete or change any automations that use a beacon's entities.
2. Go to **Settings > Devices & services > BLE Beacon Telemetry**. For each beacon, open its menu (⋮) and choose **Delete**. Home Assistant removes the beacon's device and entities with it. A linked device from another integration, such as Bermuda, stays.
3. Remove the integration:
   - **HACS:** open **HACS**, find **BLE Beacon Telemetry**, open its menu (⋮) and choose **Remove**.
   - **Without HACS:** delete the `custom_components/ble_beacon_telemetry` folder from your config folder.
4. Restart Home Assistant.

If you ignored a discovered beacon instead of adding it, it stays in the list of ignored devices. Go to **Settings > Devices & services**, select **Ignored** in the filters, and choose **Stop ignoring** on the beacon.

If you set a proxy to Active scanning only for these beacons, you can set it back to Auto.

## Supporting a new device

Support for a new device goes in its own folder, `custom_components/ble_beacon_telemetry/devices/<device_id>/`, with its tests in `tests/devices/<device_id>/`. The rest of the integration is shared. [docs/adding-a-device](docs/adding-a-device/README.md) walks through it, from capturing the device's adverts to opening a pull request with real-world test evidence. It is written so an AI coding agent can follow it too.

## Development

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest
```

## License

MIT. This project isn't affiliated with HolyIOT or any other beacon maker.
