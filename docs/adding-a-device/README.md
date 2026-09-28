# Adding a device

[SKILL.md](SKILL.md) is a step-by-step guide to adding support for a new Bluetooth device, from finding it over Bluetooth to opening a pull request with real-world test evidence. It's written for an AI coding agent working with the device's owner, and a person can follow it too.

To use it with an agent, open this repo in the agent's tool and ask it to follow `docs/adding-a-device/SKILL.md`, naming the device you want to add. Agents that load skills from a folder can load it directly.

This folder also has:

- `ha_tool.py`: finds the device, watches its adverts and reads Home Assistant's logs through Home Assistant's API, with MAC addresses replaced by labels.
- `template/`: a device folder and its tests, to copy and fill in.
