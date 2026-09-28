"""The brand images Home Assistant and HACS read from the integration folder."""

from pathlib import Path

import pytest
from PIL import Image

BRAND = Path(__file__).parents[2] / "custom_components" / "ble_beacon_telemetry" / "brand"


@pytest.mark.parametrize(("name", "size"), [("icon.png", 256), ("icon@2x.png", 512)])
def test_brand_image_is_a_transparent_square_png(name: str, size: int) -> None:
    with Image.open(BRAND / name) as image:
        assert (image.format, image.size, image.mode) == ("PNG", (size, size), "RGBA")
