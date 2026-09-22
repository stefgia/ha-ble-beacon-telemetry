"""Sample adverts from DEVICE NAME, captured from real devices with the MAC replaced.

Replace the MAC everywhere it appears, including inside payloads, with a
TEST_ADDRESSES entry from tests/conftest.py. The contract test checks this.
"""

from __future__ import annotations

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from custom_components.holyiot_ble.devices.my_device.parser import SERVICE_UUID  # TODO

from ...conftest import ADDRESS, PROXY_A, advert

PAYLOAD = bytes.fromhex("0050")  # TODO: a captured payload


def my_device_advert(
    data: bytes = PAYLOAD, *, source: str = PROXY_A, at: float | None = None
) -> BluetoothServiceInfoBleak:
    """An advert from the device, as a proxy passes it on."""
    return advert(
        address=ADDRESS,
        name="TODO",  # the name it broadcasts
        service_data={SERVICE_UUID: data},
        source=source,
        at=at,
    )


# Every kind of advert the device sends that it should claim.
ADVERTS = [my_device_advert()]
