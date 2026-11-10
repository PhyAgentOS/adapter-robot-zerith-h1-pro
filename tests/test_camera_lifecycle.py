from types import SimpleNamespace
from unittest import mock

import pytest
from zerith_h1_pro import camera_main


def run_camera(events=None, registration_error=None):
    driver = mock.Mock()
    node = mock.MagicMock()
    node.__iter__.return_value = iter(events or [])
    config = SimpleNamespace(
        cameras=[], sdk_root=None, camera_grpc_target="unused", image_fps=30
    )
    with (
        mock.patch.object(camera_main, "load_config", return_value=config),
        mock.patch.object(camera_main, "ZerithH1ProCameraDriver", return_value=driver),
        mock.patch.object(
            camera_main, "Node", return_value=node, side_effect=registration_error
        ),
    ):
        try:
            result = camera_main._run_node(None)
        finally:
            driver.disconnect.assert_called_once_with()
    return result


def test_failed_dora_registration_disconnects_camera():
    with pytest.raises(RuntimeError, match="registration failed"):
        run_camera(registration_error=RuntimeError("registration failed"))


def test_dora_error_is_a_failed_camera_run():
    assert run_camera([{"type": "ERROR", "error": "transport failed"}]) == 1


def test_normal_stop_disconnects_camera():
    assert run_camera([{"type": "STOP"}]) == 0
