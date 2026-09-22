# HolyIOT Beacon

The HolyIOT nRF52810 button tag: a small coin-cell (CR2032) tag with one button, sold as a key finder or presence beacon. It advertises as `Holy-IOT` or `Holy-IOT-S`.

Tested on two tags in 2026, with ESPHome Bluetooth proxies and Home Assistant 2026.9.

## Entities

| Entity | Key | What it does |
| --- | --- | --- |
| Battery | `battery` | Battery level in percent, smoothed (see below). |
| Button | `button` | Fires `long_press` when the button is held for about 5 seconds. |

## How the tag advertises

Each advert carries an iBeacon frame (Apple manufacturer data, or `0xFFFF` on some tags) with the factory UUID `fda50693-a4e2-4fb1-afcf-c6eb07647825`. That frame has nothing this integration uses.

The scan response carries the tag's name and a 13-byte service data frame under UUID `0x5242`:

| Bytes | Meaning |
| --- | --- |
| 0 | `0x41` |
| 1 | Battery, percent |
| 2-7 | The tag's own MAC, most significant byte first |
| 8 | `0x02` or `0x03`, meaning unknown |
| 9 | `0x06`, meaning unknown |
| 10 | Measurement type. `6` is a button. |
| 11 | Button flag: `1` for a few seconds after a long press, else `0` |
| 12 | `0x00` |

Example, a tag at 79 % with the button flag off:

```
41 4f c0 ff ee 00 12 34 02 06 06 00 00
```

Because the frame is only in the scan response, a proxy has to scan actively to hear it. On Auto, the integration asks for a 10-second active window every 5 minutes.

## Behaviour found by testing

- **Short presses are never reported.** Holding the button for about 5 seconds sets the flag; 3 seconds is not enough.
- **The flag stays on for 4 to 19 seconds**, across one or two frame updates, so it counts as one press. The tag rewrites the frame about every 5 to 10 seconds.
- **Two long presses 10 seconds apart are both reported.**
- **The battery reading jitters** by about ±3 % between frames.
- **The battery reading sags to about 35 %** while the button flag is on, and for one frame after, then recovers.

The tracker handles these with the shared building blocks in `tracking.py`:

- `LatchedPress` turns the flag into one `long_press` per press, counting a press only when a proxy sees the flag change from off to on, and counting presses less than 3 seconds apart once.
- `SmoothedLevel` reports the median of the last 10 battery readings, moving only in steps of 5 % or more. Readings taken while the flag is on are skipped.

## Which frames this device claims

Other HolyIOT tags send the same `0x5242` frame with another measurement type in byte 10. Passive BLE Monitor's parser lists 1 temperature, 2 pressure, 3 humidity, 4 vibration and 5 side (orientation). This device only claims frames with type 6, so those tags are left for a device of their own. None of them has been tested with this integration.

## Configuring the tag

The HolyIOT app (or nRF Connect) can change the advertising interval, transmit power and iBeacon fields. The default connection password is `AA14061112`. At a 500 ms advertising interval, proxies lost the tag for 20 to 45 minutes at a time. 80 ms and 160 ms were reliable.

## Sources

- Passive BLE Monitor's HolyIOT parser: https://github.com/custom-components/ble_monitor/blob/master/custom_components/ble_monitor/ble_parser/holyiot.py
- Home Assistant community thread on the nRF52810 button tag: https://community.home-assistant.io/t/holyiot-nrf52810-with-push-button-question/765735
- Live captures from two tags through ESPHome proxies (September 2026).
