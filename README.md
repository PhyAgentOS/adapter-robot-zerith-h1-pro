# Zerith H1 Pro

[English](README.md) | [简体中文](README_zh.md)

[Robot configuration description](description.md)

Standalone Forge robot package for Zerith H1 Pro, with the hardware driver, Python 3.12 SDK runtime, CLI, simulation assets and minimal Dora hardware/simulation examples.

## Version and environment

This is version **2.0.0**, targeting Forge 2.x / Dora 1.x. **BREAKING CHANGE:** do not mix this node with Forge 1.x / Dora 0.4.x nodes. Callers, message producers/consumers and `adapter-forge-gateway` must use the same compatibility line. Keep legacy deployments on `stable/1.x`.

- Python 3.12; frozen dependencies use Dora 1.0.1, Forge Common 2.1.0, Msgs 2.1.0, Robot 2.0.0 and Pillow 13.
- Msgs 2.1.0 supports Pillow 13, removing the old Msgs/Pillow upper-bound conflict. Builds use a security-fixed setuptools version.
- The vendor SDK contains Linux x86_64 / CPython 3.12 native libraries. macOS supports some software tests, but cannot load these `.so` files or qualify Linux hardware operation. The camera-only entrypoint has the same SDK platform requirement.
- Use `uv sync --frozen`. PyInstaller also uses `uv.lock` and public packages, without a neighboring Forge source tree or a fresh unpinned dependency resolution.
- Existing simulation assets and node entrypoints are retained. Dependency migration does not establish hardware, sustained-run or rollback acceptance. Run each entrypoint separately with `dora run`; every chained test must include a compatible `adapter-forge-gateway`.

## Quick checks

```bash
uv sync --frozen --python 3.12
uv run robots-zerith-h1-pro --help
uv run python -c "from zerith_h1_pro.driver import ZerithH1ProDriver"
```

Start hardware configuration from `config/config.yaml` or `config/config.example.yaml`. `sdk_root` is optional: development defaults to `third_party/H1_SDK_1.3.7` in this package, and the PyInstaller node embeds that SDK version.

`move-actuator` is intentionally **LOW_LEVEL-only**. Passing `--control-mode gravity_compensation_level` is rejected before driver construction or SDK loading; the command never automatically restores or switches to gravity compensation mode.

Source responsibilities: `config.py` owns public configuration/defaults; `actuators.py` owns actuator metadata/conversions; `sdk.py` and `camera_io.py` own lazy SDK I/O; `ipc.py` owns IPC encoding; `workers.py` owns subprocess workers; `subprocess_node.py` coordinates the parent Dora process. Robot state and safety logic remain in `driver.py`.

### Lifecycle positions

`positions` accepts only `initial` and `reset`. A follower moves to `initial` after connection initialization. Disconnect first stops chassis locomotion, confirms stopping, then calls `move_to_reset_position()` to reach `reset` before releasing control.

### Gripper direction

The H1 SDK 1.3.7 examples define `MOTOR_LEFT_ARM_8` / `MOTOR_RIGHT_ARM_8` position `0.0` as open and `1.5` as closed. Forge exposes physical opening: `0.08 m` open and `0.0 m` closed. The driver applies an inverse linear conversion:

| Forge opening | SDK Position | State |
| ---: | ---: | --- |
| `0.08 m` | `0.0` | Open |
| `0.0 m` | `1.5` | Closed |

Low-level commands and state use the vendor examples' `setMotorControl_low` / `getMotorState`. Feedback velocity is converted to metres per second with reversed sign, so positive velocity always means increasing opening.

### Mobile base

The `JointCommand`/`JointState` contract retains `wheel_left` and `wheel_right` velocity actuators alongside 21 position actuators (23 total). The node also accepts standard Forge `locomotion_command` (`forge_msgs.LocomotionCommand`): `vx` is forward metres per second, `vy` is unsupported by the differential drive and forced to zero, and `wz` is counterclockwise radians per second. A follower acts only when the actual SDK mode is `LOW_LEVEL`; chassis control uses dual-wheel `setChassis_low`, not the vendor high-level movement API.

`vx/wz` are limited before differential-drive conversion. Mixed commands exceeding wheel limits scale both wheels together to preserve curvature. Direct wheel `JointCommand` must provide both wheel velocities. Both inputs share LOW_LEVEL writes, mode locking and the watchdog. Nonzero commands must refresh faster than `locomotion_command_timeout_seconds`; explicit zero commands and `disconnect()` also send zero speed to both wheels.

```yaml
wheel_radius_m: 0.0835
wheel_track_width_m: 0.379
locomotion_max_vx_mps: 0.08
locomotion_max_wz_radps: 0.4
locomotion_max_wheel_speed_radps: 1.0
locomotion_command_timeout_seconds: 0.25
```

Wheel radius and track width come from the delivered model. Validate effective rolling radius, steering direction and slip before hardware use. The vendored SDK calls the wheel field `Speed` without specifying units or declaring its example `±1` a hardware limit. The project currently interprets it as wheel rad/s and uses `1.0` as a conservative project limit; confirm this against `Speed_Actual` and measured position derivatives with wheels safely raised. Route the `LocomotionCommand` source directly to `locomotion_command`. Chassis commands have a separate latest-only IPC queue and take priority over at most one joint command per iteration. IPC receive time counts toward watchdog freshness, preventing stale nonzero commands from restarting the base.

## Software validation

```bash
uv lock --check
uv sync --frozen --extra test --python 3.12
uv run --frozen pytest tests -q
uv build
uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file requirements-audit.txt
uvx --python 3.12 pip-audit --requirement requirements-audit.txt
```

CI retains dependency auditing and checks the existing robot executable built with frozen dependencies, including `--help` startup. The camera command remains an independent troubleshooting entrypoint in the source/installed package; this change adds no camera binary distribution.

## Package the Dora node

```bash
./scripts/build_pyinstaller.sh
# Output: dist/robots_zerith_h1_pro
dist/robots_zerith_h1_pro --help
```

## Dora examples

- Minimal hardware example: `examples/02_dora_tests/hardware_minimal`
- Minimal simulation example: `examples/03_workflows/simulation/mujoco_H1_PRO/dataflow.minimal_v2.yaml`

Both examples use Forge runtime binaries and route image/state through `task_robot` before viewers/downstream nodes. Align their peer versions before running them.

The minimal hardware example exposes one `zerith_h1_pro` node to Dora. Loading the H1 robot and camera SDKs in one process causes native `exit 139`, so `src/robots_zerith_h1_pro/main.py` uses isolated robot/camera subprocesses. The parent emits `joint_state` and image topics to `task_robot`. `src/robots_zerith_h1_pro/camera_main.py` remains a camera-only troubleshooting entrypoint, outside the default example chain.

## Delivered content

| Content | Path |
| --- | --- |
| MJCF and meshes | `assets/mjcf/`; simulation entry `scene.xml`, main model `H1_PRO.xml` |
| URDF | `assets/urdf/`; view with tools such as [RobotsFan](https://viewer.robotsfan.com/) |
| GLB visualization assets | `assets/glb/` |
| Simulation examples | `examples/03_workflows/simulation/mujoco_H1_PRO/` |
| Configuration/calibration templates | `config/` |

The repository provides its own Zerith H1 Pro simulation example; `simulator.yaml` points to `assets/mjcf/scene.xml`. A dedicated upstream `forge_runtime` `mujoco_assets` example was not identified in the original integration.

## Directory layout

| Path | Purpose |
| --- | --- |
| `assets/urdf/` | URDF assets |
| `assets/mjcf/` | MJCF, meshes, scene and model images |
| `assets/glb/` | Web/visualization GLB |
| `examples/01_sdk_tests/` | Direct vendor/driver tests independent of Forge |
| `examples/02_dora_tests/` | Dora node/topic integration tests |
| `examples/03_workflows/` | Simulation, hardware, mirrored control and VR workflows |
| `src/` | Forge robot node source |
| `scripts/` | MJCF validation and node packaging |
| `config/` | Ports, cameras, joint ordering and VR calibration |

## Assets and simulation integration

The MJCF, meshes, URDF and GLB are stored in this repository. Use `assets/` as the delivered source of truth; ordinary development, CI and simulation examples do not require an external asset repository.

- MuJoCo entry: `assets/mjcf/scene.xml`, with attach prefix `item_1/`.
- Visualization asset: `assets/glb/H1_PRO.glb`.
- URDF: `assets/urdf/`, corresponding to the MJCF model.

See `examples/03_workflows/simulation/SIMULATION_INTEGRATION.md` for commands and Forge runtime integration. The sequence is asset validation → `verify_mjcf` → convention alignment → the in-repository simulation example (`model_path` referencing this repository's scene, `prefix: item_1/`, 25 actuators matching `task_robot`) → automated sweeps and visual smoke checks → comparison with hardware. See `examples/03_workflows/simulation/JOINT_SWEEP_CHECKLIST.md` for check records.

Node implementations belong in `src/`; packaging, validation and asset-generation helpers belong in `scripts/`. Simulation examples reuse generic MuJoCo/TaskRobot nodes. Record additional implementations and entrypoints in `src/README.md`.

## Delivery and acceptance

Existing delivery records cover simulation assets and Forge/Dora simulation workflows. Hardware direction/zero/limit checks, VR/mirrored-control parameters and deployment acceptance still need verification. Record completed checks and commands alongside the applicable configuration or workflow; software checks alone do not establish hardware acceptance.

## Versioned releases

**Mandatory tag-first release rule:** merge the version/lock change, create an annotated version tag on that reviewed commit, build that exact tag, validate the artifacts, then publish. Moving branch names, untagged commit IDs and replacement of published tags are not release inputs.

| Release line | Source | Node/package version | Runtime |
| --- | --- | --- | --- |
| Forge 1.x | `stable/1.x` | `1.x`, tag `v1.X.Y` | Forge 1.x / Dora 0.4.x |
| Forge 2.x | `main` | `2.x`, tag `v2.X.Y` | Forge 2.x / Dora 1.x |

**Legacy normalization:** nodes previously at 0.x on `stable/1.x` release as **1.0.0**, retaining Forge 1.x / Dora 0.4.x dependencies and runtime behavior. Existing 1.x package versions are retained. Node/package majors now follow the Forge compatibility line; a 0.x tag is rejected.

The default branch uses Forge 2.x; maintain Forge 1.x releases from `stable/1.x`.

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
