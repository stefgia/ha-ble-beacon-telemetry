---
name: add-beacon-device
description: Add support for a new Bluetooth beacon to the BLE Beacon Telemetry Home Assistant integration. Covers connecting to Home Assistant, capturing and decoding the device's adverts, researching it, writing the device folder and tests, testing it on real hardware and opening a pull request with evidence.
---

# Adding a device

This guide takes a Bluetooth device that the integration doesn't support yet, and ends with a pull request that adds it. It's written for an AI coding agent working with a person who owns the device, and a person can follow it just as well. "You" is the agent; "the owner" is the person with the device and the Home Assistant instance.

Work through the steps in order. Each ends with something to check before moving on.

## Rules that apply throughout

- **Privacy.** Never write a real MAC address, token, Home Assistant address or personal name into the repo, a commit or a pull request. Use the labels `ha_tool.py` prints ("Device 1", "Proxy 1") when you talk about devices, and the test MACs in `tests/conftest.py` in code and samples.
- **Ask before changing the owner's Home Assistant.** Changing a proxy's scanning mode, installing the integration, restarting Home Assistant and adding or deleting config entries all need the owner's go-ahead each time.
- **Nothing is known until it's tested on the device.** Documentation and other projects' parsers are hypotheses. The pull request needs real-world evidence (step 9), not only passing unit tests.
- **Device code stays in the device's folder.** Change shared code only when the device can't be supported otherwise, in a separate commit, and say why in the pull request.
- **Never change a released device's `id` or entity keys.** They're stored in users' config entries and entity IDs.

## 1. Set up the repo

```bash
git clone https://github.com/stefgia/ha-ble-beacon-telemetry
cd ha-ble-beacon-telemetry
git checkout -b add-<device_id>
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest
```

`<device_id>` is a short lowercase name for the model, starting with the maker, such as `holyiot_th_sensor` or `minew_e8`. It becomes the folder name.

**Check:** all tests pass before you change anything.

## 2. Connect to Home Assistant

`ha_tool.py`, next to this guide, talks to Home Assistant's API. It needs the Home Assistant address and a long-lived access token. Ask the owner to create the token:

1. In Home Assistant, open the profile page (the user icon at the bottom of the sidebar).
2. Open the **Security** tab.
3. Under **Long-lived access tokens**, select **Create token**, name it (for example "adding a device") and copy it. It's shown only once.

The owner sets both in the shell you run commands in. They go in the environment only, never in a file in the repo:

```bash
export HA_URL=http://homeassistant.local:8123
export HA_TOKEN=<the token>
```

The token can do anything the owner's account can. Tell the owner to delete it (same page) when the work is done.

**Check:**

```bash
.venv/bin/python docs/adding-a-device/ha_tool.py check
```

prints the Home Assistant version and the number of Bluetooth adapters and proxies. If it's 0, the owner needs a Bluetooth adapter or an ESPHome Bluetooth proxy first.

## 3. Find the device

The device must be near a proxy and switched on. Ask the owner to hold it close to one proxy, then run:

```bash
.venv/bin/python docs/adding-a-device/ha_tool.py list --seconds 60
```

It lists every device Home Assistant hears, strongest signal first, with its label, the proxy that heard it, its broadcast name and its data. Many beacons broadcast a name with the maker or model in it, such as `Holy-IOT`. If there are several candidates, ask the owner to move the device away and run `list` again: the one whose signal drops is it. Note its label, such as "Device 4".

`list` output shows the names nearby devices broadcast, which can be personal. Keep it out of the pull request.

**Check:** you know the device's label, and the owner agrees it's the right device.

## 4. Capture how it behaves

### Get the full data

Many devices send their useful data only in the scan response, which proxies hear only while they scan actively. ESPHome proxies default to Auto, which scans actively for a few seconds now and then. Ask the owner to set the proxy nearest the device to **Active** for the capture: **Settings > Devices & services > ESPHome > (the proxy) > Configure > Bluetooth scanning mode**. Note the original setting, so it can be put back at the end.

### Watch the adverts

```bash
.venv/bin/python docs/adding-a-device/ha_tool.py watch "Device 4" --seconds 600
```

Each line is a change in one of the device's data fields: time, proxy, signal, the field (`service 5242` is service data under UUID 0x5242, `manufacturer 0x004c` is Apple's, used by iBeacon) and the bytes. The device's own MAC inside a payload shows as `[Device 4 MAC: bytes 2-7]`. When a field changes, the line ends with the bytes that changed, such as `changed: byte 11 00->01`.

Home Assistant only passes on adverts whose content changed. No line means nothing changed, not that nothing was sent.

### Run experiments

Ask the owner to do one thing at a time and tell you the time they did it. Start with doing nothing for two minutes, to see which bytes change on their own (counters, battery jitter). Then, depending on the device:

- Buttons: a short press, a long press (hold 5 seconds), a double press, each separately with 20 seconds between.
- Temperature or humidity: hold it in a hand, breathe on it, put it in the fridge for 5 minutes.
- Motion or orientation: move it, turn it over, leave it still.
- Anything else the device claims to measure.

Match each action to the changes that followed it. Record the captured payloads with their meaning; they become the test samples.

Things to look for:

- Which bytes are fixed, which count, which carry values, and whether values are signed, little or big endian, or scaled.
- Flags that stay on for a while after an event, and how long.
- Readings that jump or sag, for example while the device transmits or lights an LED.
- Actions that change nothing at all. Say so in the README; it saves the next person time.

### Read Home Assistant's logs

Once your branch is installed in Home Assistant (step 9), its debug log shows every advert a configured device sends, and every discovered device that no model claimed. A device only counts as discovered if its adverts match a filter in `manifest.json`, so add yours there first (step 6). Turn it on, read it, and turn it off:

```bash
.venv/bin/python docs/adding-a-device/ha_tool.py debug on
.venv/bin/python docs/adding-a-device/ha_tool.py logs --grep ble_beacon_telemetry
.venv/bin/python docs/adding-a-device/ha_tool.py debug off
```

`logs` replaces MACs with labels. Turn debug logging off when done; it's verbose.

**Check:** you can explain every byte that changed, or you've listed it as unknown.

## 5. Research the device

Search for what others have found, and treat every claim as a hypothesis to test against your captures:

- The maker's product page and datasheet, found by the model number printed on the device or its box.
- Other projects' decoders: Passive BLE Monitor (`custom-components/ble_monitor`, one parser per maker in `ble_parser/`), Theengs Decoder (`theengs/decoder`), and ESPHome configs on GitHub that mention the service UUID or manufacturer ID.
- Home Assistant community and ESPHome forum threads about the model.
- The standard frame the device may use, such as Eddystone TLM (service UUID `0xFEAA`), which many makers use for battery and temperature. If a device folder already reads that frame, extend it rather than adding another.

Useful searches: the model number with "BLE" or "advertising", the service UUID or manufacturer ID, and the broadcast name.

Where a source and your captures disagree, trust the captures and write the difference in the README. Keep the links; they go in the README's Sources section.

**Check:** a byte layout that explains every capture, with a source or a capture behind each field.

## 6. Write the code

Copy the template into place:

```bash
cp -r docs/adding-a-device/template/device custom_components/ble_beacon_telemetry/devices/<device_id>
mkdir -p tests/devices/<device_id>
cp docs/adding-a-device/template/tests/* tests/devices/<device_id>/
```

Then replace every `TODO`:

1. **`parser.py`**: a pure function from bytes to a reading. Reject anything that doesn't fit exactly (length, fixed bytes, the MAC if the payload repeats it, value ranges), so the device never claims another model's data. Document the byte layout in the module docstring.
2. **`__init__.py`**: the `Device` subclass and its `Tracker`. The interfaces are in `custom_components/ble_beacon_telemetry/device.py`; read its docstrings.
   - `id` is the folder name. `name` is the model name and `manufacturer` the maker, both shown in Home Assistant.
   - `discovery` lists the advert filters Home Assistant uses to find the device, with the keys of the `bluetooth` list in `manifest.json`.
   - `matches()` must be specific. Models, sometimes from different makers, can share a service UUID or manufacturer ID and differ only in the content. `devices/holyiot_button_tag` claims HolyIOT's `0x5242` frame only when it reports a button, for example. The contract test fails if two devices claim the same sample.
   - Describe entities with Home Assistant's `SensorEntityDescription` and `EventEntityDescription`. Use a `device_class` where one fits; it names the entity and sets its icon and unit handling.
   - Put stateful handling in the tracker. `tracking.py` has `SmoothedLevel` for jittery readings and `LatchedPress` for flags that stay on after an event. Use them before writing your own.
3. **Register the device**: import it in `custom_components/ble_beacon_telemetry/devices/__init__.py` and add it to `DEVICES`.
4. **`manifest.json`**: add each `discovery` filter to the `bluetooth` list if it isn't there already.
5. **`strings.json` and `translations/en.json`** (keep them identical): for each entity with a `translation_key`, add its name under `entity.<platform>.<key>`, and for events, the name of each event type.

**Check:** the code imports, and `matches()` is true for your captured adverts and false for other devices' adverts.

## 7. Write the tests

1. **`samples.py`**: the adverts you captured, as `advert()` calls. Use `ADDRESS` from `tests/conftest.py` for the MAC, and replace the MAC inside any payload that repeats it. `ADVERTS` lists one of each kind the device sends.
2. **`test_device.py`**: `matches()` on your samples and on other adverts, and one test per behaviour you found in step 4, using the captures that showed it.
3. Add parser tests for each field and each kind of payload it must reject.

```bash
.venv/bin/python -m pytest
```

`tests/devices/test_contract.py` runs for every device. It checks the README and its row in the main README, the manufacturer, the manifest, entity names, the samples and that they use test MACs, that no device claims another's samples, and that no `TODO` or template placeholder is left. Fix what it reports; don't change it to pass.

**Check:** all tests pass.

## 8. Write the device README

Copy `template/device/README.md` if you haven't, and fill it in: what the device is, what was tested on what, the entities, the byte layout with an example, the behaviour found by testing and how the tracker handles it, settings in the manufacturer's app that matter, and sources. The first line must be `# ` followed by the device's `name`.

Add a row for the device to the "Supported devices" table in the main `README.md`.

**Check:** someone with the device could understand from the README what they'll get, and someone without it could maintain the code.

## 9. Test on the real device

Unit tests aren't enough to merge a device. The pull request needs evidence that it works in Home Assistant with the real device.

### Install the branch

Ask the owner how they reach their Home Assistant config folder:

- With file access (Samba, SSH or a shared folder): `scripts/deploy.sh /path/to/config`.
- With HACS only: push the branch to the owner's fork, add the fork as a custom repository in HACS, and download it. If HACS doesn't offer the branch in its version list, make it the fork's default branch while testing.

Then, with the owner's go-ahead, restart Home Assistant (**Settings > System > Restart**) and add the device from **Settings > Devices & services**.

### Run the test plan

Write a short test plan: each entity, the action that should change it, and what should happen. For example:

| Entity | Action | Expected |
| --- | --- | --- |
| Battery | none, 10 minutes | a value close to the app's reading, changing no more than once |
| Button | long press, 3 times | 3 `long_press` events |
| Button | short press | no event (the device doesn't report it) |

Run `watch` for the whole test, with the proxy on the scanning mode the README recommends:

```bash
.venv/bin/python docs/adding-a-device/ha_tool.py watch "Device 4" --seconds 1200 | tee evidence.txt
```

Lines starting `ENTITY` are the integration's entities changing state. Ask the owner to do each action and note the time. Also test at least once on **Auto** if the device needs active scanning, and note what's missed.

Then put the proxy back on the scanning mode it had before step 4, unless the owner decides otherwise.

**Check:** every row of the test plan has a matching `ENTITY` line or an explained absence. Read `evidence.txt` for MACs, names and addresses before using it; `watch` output should contain none. Don't commit it.

## 10. Open the pull request

Commit on your branch with messages that say what changed and why. Push to the owner's fork and open a pull request against `main`. The repository's pull request template has these sections; fill in every one:

- **Device**: model, where it's sold, firmware or app version if known, how many units were tested.
- **What it adds**: the entities and events, and anything the device can do that isn't supported.
- **How the data was worked out**: the byte layout in short, and the sources and captures behind it.
- **Changes outside the device folder**: none, or each one with the reason.
- **Real-world testing**: Home Assistant version, the proxies and their scanning modes, the test plan with results, and the redacted `watch` output in a collapsed block (`<details>`).
- **Unit tests**: the `pytest` summary line.
- **Checklist**: the template's list, ticked honestly.

One device per pull request. If something is unverified, say so under "What it adds"; don't leave it for the reviewer to find.

**Check:** a reviewer can see what the device sends, why the code reads it that way, and that it worked on a real device, without asking.

## When you're done

- Ask the owner to delete the access token (profile > Security).
- Make sure every proxy is back on its original scanning mode, or the owner chose to leave it.
