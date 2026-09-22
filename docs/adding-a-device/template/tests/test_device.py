"""Unit tests for DEVICE NAME and its tracker, without Home Assistant."""

from custom_components.holyiot_ble.devices.my_device import (  # TODO
    MyDevice,
    MyDeviceTracker,
)

from ...conftest import advert
from .samples import PAYLOAD, my_device_advert


def test_claims_its_own_adverts_only() -> None:
    assert MyDevice().matches(my_device_advert())
    assert not MyDevice().matches(advert(name="something else"))


def test_reads_the_battery() -> None:
    update = MyDeviceTracker().update(my_device_advert(PAYLOAD))
    assert update.values == {"battery": 80}  # TODO


# TODO: one test per behaviour in the README's "Behaviour found by testing",
# using the captured payloads that showed it.
