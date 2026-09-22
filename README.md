# HolyIOT BLE

HolyIOT BLE is a Home Assistant integration for HolyIOT Bluetooth tags. It reads the data a tag broadcasts, such as its battery level or button presses, and turns it into sensors and events you can use in automations.

It works with the Bluetooth adapters and ESPHome Bluetooth proxies you already have in Home Assistant. You don't need custom proxy firmware.

## Supported devices

| Device | Entities | Details |
| --- | --- | --- |
| HolyIOT Beacon (nRF52810 button tag) | Battery, Button (long press) | [devices/holyiot_beacon](custom_components/holyiot_ble/devices/holyiot_beacon/README.md) |

Each device's page describes what it reports, how it behaves and what it was tested with. To add support for another device, see [Adding a device](#adding-a-device).

## Requirements

- Home Assistant 2026.9.0 or newer.
- A Bluetooth adapter or ESPHome Bluetooth proxy in range of the tag. Most tags need it set to Active or Auto scanning (see [Scanning modes](#scanning-modes)).

## Installation

1. In HACS, open the menu in the top right and choose **Custom repositories**.
2. Add `https://github.com/stefgia/ha-holyiot-ble` with the type **Integration**.
3. Search HACS for **HolyIOT BLE**, download it and restart Home Assistant.

Without HACS, copy the integration into your config folder and restart Home Assistant:

```bash
scripts/deploy.sh /path/to/homeassistant/config
```

## Adding a tag

Home Assistant finds tags by itself and offers them under **Settings > Devices & services**. Select **Add** on a discovered tag to set it up.

To add one by hand, go to **Settings > Devices & services > Add integration**, choose **HolyIOT BLE** and pick the tag from the list. A new tag can take a few minutes to appear on Auto scanning.

## Using it

Each tag becomes a device with the entities its [device page](#supported-devices) lists. Sensors keep their last value while the tag is out of range, and after a restart.

Events, such as a button press, show up as an event entity. To run something when one fires, use the entity's state as an automation trigger:

```yaml
triggers:
  - trigger: state
    entity_id: event.holyiot_beacon_1234_button
actions:
  - action: light.toggle
    target:
      entity_id: light.hallway
```

If another integration tracks the same tag, such as Bermuda, its device shows up as a linked device.

## Scanning modes

Many tags send their data only in the scan response, which a Bluetooth adapter or proxy hears only while it scans actively. Its scanning mode decides how much of that data reaches Home Assistant:

| Mode | Sensors | Events |
| --- | --- | --- |
| Active | Always current | Every event |
| Auto (the default for ESPHome proxies) | Update every few minutes | Only events during a short active window, so most are missed |
| Passive | Never | Never |

On Auto, the integration asks the proxy to scan actively for 10 seconds every 5 minutes for each tag. That's enough for slow sensors such as a battery level. If you use a tag's events, set at least one proxy near the tag to Active. For an ESPHome proxy, the scanning mode is in the ESPHome integration's options. Each device page says whether it needs active scanning.

## Uninstalling

Remove the tags first, then the integration. Removing the integration first leaves its tags behind as broken entries.

1. Delete or change any automations that use a tag's entities.
2. Go to **Settings > Devices & services > HolyIOT BLE**. For each tag, open its menu (⋮) and choose **Delete**. Home Assistant removes the tag's device and entities with it. A linked device from another integration, such as Bermuda, stays.
3. Remove the integration:
   - **HACS:** open **HACS**, find **HolyIOT BLE**, open its menu (⋮) and choose **Remove**.
   - **Without HACS:** delete the `custom_components/holyiot_ble` folder from your config folder.
4. Restart Home Assistant.

If you ignored a discovered tag instead of adding it, it stays in the list of ignored devices. Go to **Settings > Devices & services**, select **Ignored** in the filters, and choose **Stop ignoring** on the tag.

If you set a proxy to Active scanning only for these tags, you can set it back to Auto.

## Adding a device

Support for a new device goes in its own folder, `custom_components/holyiot_ble/devices/<device_id>/`, with its tests in `tests/devices/<device_id>/`. The rest of the integration is shared. [docs/adding-a-device](docs/adding-a-device/README.md) walks through it, from capturing the device's adverts to opening a pull request with real-world test evidence. It is written so an AI coding agent can follow it too.

## Development

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest
```

## License

MIT
