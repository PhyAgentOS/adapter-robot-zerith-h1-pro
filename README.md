# Zerith H1 Pro

[English](README.md) | [简体中文](README_zh.md)

Zerith H1 Pro driver, Python 3.12 SDK runtime, CLI and Forge/Dora hardware and simulation examples.

## Setup

```bash
uv sync
uv run robots-zerith-h1-pro --help
uv run python -c "from zerith_h1_pro.driver import ZerithH1ProDriver"
./scripts/build_pyinstaller.sh
```

Start with `config/config.example.yaml` or `config/config.yaml`. The default SDK is `third_party/H1_SDK_1.3.7`; the PyInstaller artifact bundles this SDK. `move-actuator` is LOW_LEVEL-only and rejects gravity-compensation mode before SDK loading. Follower initialization moves to `initial`. Disconnect first confirms locomotion has stopped, then uses `move_to_reset_position()` before releasing control; only `initial` and `reset` position keys are supported.

## Joint and locomotion contracts

Forge gripper opening uses metres: `0.08` is open and `0.0` closed, opposite to SDK Position `0.0` open / `1.5` closed. Velocity conversion keeps increasing opening positive. SDK access uses `setMotorControl_low` / `getMotorState`.

The joint interface contains 21 position actuators and `wheel_left`/`wheel_right` velocity actuators. `locomotion_command` accepts `forge_msgs.LocomotionCommand`: forward `vx` in m/s, `vy` forced to zero and counterclockwise `wz` in rad/s. Motion requires actual LOW_LEVEL mode and calls `setChassis_low`. Wheel commands must specify both wheels; direct and locomotion commands share mode checks, wheel limits and a watchdog. Stale nonzero commands cannot restart the chassis. Configuration defaults include radius `0.0835 m`, track width `0.379 m`, `vx=0.08 m/s`, `wz=0.4 rad/s`, wheel limit `1.0 rad/s`, timeout `0.25 s`. These are conservative project limits, not manufacturer-certified bounds; verify direction, rolling geometry and actual speed with lifted wheels before hardware use.

## Examples and assets

- Hardware entry: `examples/02_dora_tests/hardware_minimal`.
- Simulation: `examples/03_workflows/simulation/mujoco_H1_PRO/dataflow.minimal_v2.yaml`.
- [Simulation integration](examples/03_workflows/simulation/SIMULATION_INTEGRATION.md) and [checklist](examples/03_workflows/simulation/JOINT_SWEEP_CHECKLIST.md).
- [Robot description](description.md), `assets/mjcf/scene.xml`, `assets/urdf/` and `assets/glb/H1_PRO.glb`.

The hardware node isolates robot and camera SDKs in subprocesses because loading both in one process can cause native exit 139. `subprocess_node.py` coordinates Dora; `driver.py` retains state and safety behavior. The simulation model uses `prefix: item_1/`; align model actuator configuration with TaskRobot. Asset delivery and historical simulations do not establish current hardware, VR calibration, direction, zero-position or limit acceptance. Preserve the repository and vendored asset licenses.

## Versioned releases

**Mandatory tag-first release rule:** merge the version/lock change, create an annotated version tag on that reviewed commit, build that exact tag, validate the artifacts, then publish. Moving branch names, untagged commit IDs and replacement of published tags are not release inputs.

| Release line | Source | Node/package version | Runtime |
| --- | --- | --- | --- |
| Forge 1.x | `stable/1.x` | `1.x`, tag `v1.X.Y` | Forge 1.x / Dora 0.4.x |
| Forge 2.x | `main` | `2.x`, tag `v2.X.Y` | Forge 2.x / Dora 1.x |

**Legacy normalization:** nodes previously at 0.x on `stable/1.x` release as **1.0.0**, retaining Forge 1.x / Dora 0.4.x dependencies and runtime behavior. Existing 1.x package versions are retained. Node/package majors now follow the Forge compatibility line; a 0.x tag is rejected.

The default branch still uses Forge 1.x; its 2.x migration must merge before a 2.x release can pass validation.

Run **Build versioned release** from `main` for either line. First merge the version/lock changes into the selected source branch, then create an unused **annotated** tag on that reviewed commit. The tag must match package metadata. Never move existing tags or reuse a published version. Dispatch uses the workflow's reviewed tooling with the exact tagged source, so legacy tags need not contain the new release helper.

```bash
# Replace with an existing, reviewed and unpublished tag matching source metadata.
TAG=v1.X.Y
gh workflow run release.yml --ref main -f release_line=1.x -f tag="$TAG"
TAG=v2.X.Y
gh workflow run release.yml --ref main -f release_line=2.x -f tag="$TAG"
```

The workflow verifies tag type, source commit, branch ancestry, source version and locked Forge/Dora compatibility. It builds source archives and wheel/sdist where supported, checks Python distribution metadata and SHA-256, and creates or attaches to a **draft GitHub Release**. Published releases/assets are not overwritten; review all build results and acceptance evidence before publishing. This workflow does not publish node packages to PyPI.

Set `build_binaries=true` to call the existing Ubuntu 20.04 binary workflow; its existing architecture, CLI and archive checks remain in force. You can also run `build-ubuntu20.yml` directly with `ref`, `version` and `release_line`; `ref` must be an annotated tag, not a moving branch. Binary artifacts are attached only after all selected jobs succeed.

The source archive preserves the tagged tree; external SDKs/submodules, model downloads and site configuration remain separate prerequisites. A dependency or SDK build failure is not successful release acceptance. Build success does not establish single-node or Gateway-chain `dora run`, hardware, real-model, sustained-run or rollback acceptance. Every acceptance chain must include `adapter-forge-gateway` from the same compatibility line. Forge 2.x is a **breaking change**: align Forge libraries, node versions and Dora across the entire deployment; keep 1.x on its maintenance branch.
