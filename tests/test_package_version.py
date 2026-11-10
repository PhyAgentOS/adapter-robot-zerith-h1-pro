from __future__ import annotations

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_and_lock_versions_match_release() -> None:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as file:
        project = tomllib.load(file)
    with (PROJECT_ROOT / "uv.lock").open("rb") as file:
        lock = tomllib.load(file)

    package = next(
        package
        for package in lock["package"]
        if package["name"] == project["project"]["name"]
    )

    assert project["project"]["version"] == "2.0.0"
    assert package["version"] == project["project"]["version"]


def test_both_entrypoints_report_package_version_without_hardware():
    from typer.testing import CliRunner
    from zerith_h1_pro import camera_main, main

    for app, binary in [
        (main.app, "robots_zerith_h1_pro"),
        (camera_main.app, "robots_zerith_h1_pro_camera"),
    ]:
        result = CliRunner().invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.stdout.strip() == f"{binary} 2.0.0"
