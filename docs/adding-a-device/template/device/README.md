# HolyIOT My Device

One paragraph: what the device is, what it looks like, how it's sold, and the name it advertises.

Tested on: how many units, which firmware or app version if known, which proxies, Home Assistant version, month and year.

## Entities

| Entity | Key | What it does |
| --- | --- | --- |
| Battery | `battery` | ... |

## How the device advertises

Which frames it sends (advert or scan response, service data UUID, manufacturer ID), and whether a proxy needs active scanning.

| Bytes | Meaning |
| --- | --- |
| 0 | ... |

An example payload, with the MAC replaced by a test MAC:

```
.. .. c0 ff ee 00 12 34 ..
```

## Behaviour found by testing

What testing showed that the documentation didn't say: jitter, delays, flags that stay on, readings that sag, values that only change on certain actions. Say how the tracker handles each one.

## Configuring the device

Settings in the manufacturer's app that change what it sends, such as advertising interval or modes, and anything that stopped it working.

## Sources

- Links to datasheets, other projects' parsers and forum threads used, and what each was used for.
- Live captures (month and year).
