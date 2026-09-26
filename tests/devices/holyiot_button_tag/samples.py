"""Sample adverts from a HolyIOT Button Tag, captured from real tags with the MAC replaced.

The contract test (tests/devices/test_contract.py) checks every device has a
samples.py with an ADVERTS list the device claims and its tracker can read.
"""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from custom_components.ble_beacon_telemetry.devices.holyiot_button_tag.parser import SERVICE_UUID

from ...conftest import ADDRESS, PROXY_A, advert

# 79 % battery, button type, flag off. Bytes 2-7 are the tag's MAC (ADDRESS).
PAYLOAD = bytes.fromhex("414fc0ffee0012340206060000")
# The scan response also carries this iBeacon frame (factory UUID, major 10011, minor 19641).
IBEACON = bytes.fromhex("0215fda50693a4e24fb1afcfc6eb07647825271b4cb9c9")


def payload(*, battery: int = 79, pressed: bool = False, measurement: int = 6) -> bytes:
    """PAYLOAD with another battery level, button flag or measurement type."""
    return (
        PAYLOAD[:1]
        + bytes([battery])
        + PAYLOAD[2:10]
        + bytes([measurement, pressed])
        + PAYLOAD[12:]
    )


def button_tag_advert(
    data: bytes = PAYLOAD, *, source: str = PROXY_A, at: float | None = None
) -> BluetoothServiceInfoBleak:
    """A scan response from the tag, as a proxy passes it on."""
    return advert(
        address=ADDRESS,
        name="Holy-IOT-S",
        service_data={SERVICE_UUID: data},
        manufacturer_data={76: IBEACON},
        source=source,
        at=at,
    )


ADVERTS = [button_tag_advert(), button_tag_advert(payload(pressed=True))]
