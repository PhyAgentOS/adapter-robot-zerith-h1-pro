"""Exercise real camera payload encoding with the locked Forge/Pillow stack."""

import cv2
import numpy as np
import pytest
from forge_msgs import CompressedImage, Image

from zerith_h1_pro.camera_io import build_color_payload, build_depth_payload
from zerith_h1_pro.config import ZerithCameraStreamConfig


@pytest.mark.parametrize("image_format", ["raw", "jpeg", "png"])
@pytest.mark.parametrize("color_order", ["rgb", "bgr"])
def test_color_payload_round_trip(image_format, color_order):
    rgb = np.full((8, 12, 3), [220, 90, 30], dtype=np.uint8)
    frame = rgb if color_order == "rgb" else rgb[..., ::-1]
    config = ZerithCameraStreamConfig(
        name="head", output_id="image/head", image_format=image_format,
        color_order=color_order,
    )

    payload = build_color_payload(frame, None, config, cv2)

    if image_format == "raw":
        message = Image.from_arrow(payload)
        assert message.encoding == color_order + "8"
        np.testing.assert_array_equal(message.to_numpy(), frame)
    else:
        message = CompressedImage.from_arrow(payload)
        assert message.format == image_format
        decoded = message.to_numpy()  # Forge decodes with Pillow.
        assert decoded.shape == rgb.shape
        np.testing.assert_allclose(decoded, rgb, atol=3 if image_format == "jpeg" else 0)


def test_raw_depth_keeps_uint16_values():
    depth = np.array([[0, 1000, 65535], [20, 300, 5000]], dtype=np.uint16)
    config = ZerithCameraStreamConfig(
        name="head", output_id="image/head", enable_depth=True,
        depth_output_id="image/depth", depth_format="raw_u16",
    )

    message = Image.from_arrow(build_depth_payload(depth, None, config, cv2))

    assert message.encoding == "16UC1"
    assert message.to_numpy().dtype == np.uint16
    np.testing.assert_array_equal(message.to_numpy().squeeze(), depth)
