# HolyIOT BLE

HolyIOT BLE is a Home Assistant integration for HolyIOT Bluetooth tags, such as the nRF52810 button tag. It adds a battery sensor and a long-press event for each tag, so you can see when a tag needs a new battery and use its button to trigger automations.

It works with the Bluetooth adapters and ESPHome Bluetooth proxies you already have in Home Assistant. You don't need custom proxy firmware.

## Requirements

- Home Assistant 2026.9.0 or newer.
- A Bluetooth adapter or ESPHome Bluetooth proxy in range of the tag, set to Active or Auto scanning (see [Scanning modes](#scanning-modes)).

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

Each tag becomes a device with two entities:

| Entity | What it does |
| --- | --- |
| Battery | The battery level in percent. It changes in steps of 5 % or more, so the tag's small jumps between readings don't show. It keeps the last level while the tag is out of range, and after a restart. |
| Button | Fires a `long_press` event when you hold the button for about 3 seconds. |

The tags don't report short presses, only a long press. After one, wait a few seconds before the next, or the two can count as one.

To run something on a long press, create an automation with the Button entity's state as the trigger:

```yaml
triggers:
  - trigger: state
    entity_id: event.holyiot_1234_button
actions:
  - action: light.toggle
    target:
      entity_id: light.hallway
```

If another integration tracks the same tag, such as Bermuda, its device shows up as a linked device.

## Scanning modes

The battery and button data only reach Home Assistant while a Bluetooth adapter or proxy scans actively. Its scanning mode decides how much you get:

| Mode | Battery | Button |
| --- | --- | --- |
| Active | Always current | Every long press |
| Auto (the default for ESPHome proxies) | Updates every few minutes | Only long presses during a short active window, so most are missed |
| Passive | Never | Never |

On Auto, the integration asks the proxy to scan actively for 10 seconds every 5 minutes for each tag. That's enough for the battery. If you use the button, set at least one proxy near the tag to Active. For an ESPHome proxy, the scanning mode is in the ESPHome integration's options.

## Uninstalling

Remove the tags first, then the integration. Removing the integration first leaves its tags behind as broken entries.

1. Delete or change any automations that use a tag's Button or Battery entity.
2. Go to **Settings > Devices & services > HolyIOT BLE**. For each tag, open its menu (⋮) and choose **Delete**. Home Assistant removes the tag's device and entities with it. A linked device from another integration, such as Bermuda, stays.
3. Remove the integration:
   - **HACS:** open **HACS**, find **HolyIOT BLE**, open its menu (⋮) and choose **Remove**.
   - **Without HACS:** delete the `custom_components/holyiot_ble` folder from your config folder.
4. Restart Home Assistant.

If you ignored a discovered tag instead of adding it, it stays in the list of ignored devices. Go to **Settings > Devices & services**, select **Ignored** in the filters, and choose **Stop ignoring** on the tag.

If you set a proxy to Active scanning only for the button, you can set it back to Auto.

## Development

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest
```

## License

MIT
