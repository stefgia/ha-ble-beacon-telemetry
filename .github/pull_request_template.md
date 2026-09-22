<!--
Adding a device? Follow docs/adding-a-device/SKILL.md and fill in every section.
For other changes, describe the change and why, and delete the sections that don't apply.
Never paste real MAC addresses, tokens, Home Assistant addresses or personal names.
-->

## Device

- Model:
- Where it's sold:
- Firmware or app version (if known):
- Units tested:

## What it adds

<!-- Entities and events, and anything the device does that isn't supported. Say what is unverified. -->

## How the data was worked out

<!-- The byte layout in short, and the sources and captures behind each field. -->

## Changes outside the device folder

<!-- "None", or each change with the reason. -->

## Real-world testing

- Home Assistant version:
- Proxies and their scanning modes:

| Entity | Action | Expected | Result |
| --- | --- | --- | --- |
|  |  |  |  |

<details>
<summary>Redacted <code>ha_tool.py watch</code> output</summary>

```
paste here
```

</details>

## Unit tests

```
paste the pytest summary line
```

## Checklist

- [ ] Device code is in `custom_components/holyiot_ble/devices/<device_id>/` and its tests in `tests/devices/<device_id>/`.
- [ ] The device has a README, and a row in the main README's "Supported devices" table.
- [ ] Discovery filters are in `manifest.json`; entity and event names are in `strings.json` and `translations/en.json`.
- [ ] Samples come from real captures, with MACs replaced by test MACs (payloads included).
- [ ] No released device `id` or entity key changed.
- [ ] Tested on a real device in Home Assistant, with the evidence above.
- [ ] `pytest` passes.
- [ ] No real MACs, tokens, addresses or personal names anywhere in the change or this description.
