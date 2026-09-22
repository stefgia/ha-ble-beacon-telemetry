# HolyIOT BLE

HolyIOT BLE is a Home Assistant integration for HolyIOT Bluetooth tags, such as the nRF52810 button tag. It adds a battery sensor and a button event for each tag, so you can see when a tag needs a new battery and use its button to trigger automations.

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
| Battery | The battery level in percent. It keeps the last level while the tag is out of range, and after a restart. |
| Button | Fires a `press` event each time the button is pressed. |

To run something when the button is pressed, create an automation with the Button entity's state as the trigger:

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
| Active | Always current | Every press |
| Auto (the default for ESPHome proxies) | Updates every few minutes | Only presses during a short active window, so most are missed |
| Passive | Never | Never |

On Auto, the integration asks the proxy to scan actively for 10 seconds every 5 minutes for each tag. That's enough for the battery. If you use the button, set at least one proxy near the tag to Active. For an ESPHome proxy, the scanning mode is in the ESPHome integration's options.

## Development

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest
```

## License

MIT
