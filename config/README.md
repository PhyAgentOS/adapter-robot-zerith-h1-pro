# 配置与标定

- **仿真 / 真机**：关节顺序、左右臂命名前缀、`item_1/` 等与 MuJoCo 模型一致的字段，放在此目录的 YAML 中（勿提交密钥）。
- **VR / 同构**：填写 `vr_calibration.yaml.example` 后另存为 `vr_calibration.yaml`（敏感标定勿入库）。

零次方 Zerith H1_PRO 含移动底盘、头部、双臂与夹爪，标定与验收需分系统记录。夹爪 YAML 值使用 opening 米制语义：`0.08` 张开、`0.0` 闭合；driver 内部反向换算为厂商 SDK 的 `Position=0.0` 张开、`Position=1.5` 闭合。

移动底盘必须显式配置 `wheel_radius_m`、`wheel_track_width_m`、`locomotion_max_vx_mps`、`locomotion_max_wz_radps`、`locomotion_max_wheel_speed_radps` 和 `locomotion_command_timeout_seconds`。示例中的 `0.0835m` 轮半径与 `0.379m` 轮距来自交付模型。默认线速度上限为 `0.30 m/s`，角速度上限为 `1.00 rad/s`，轮速上限为 `5.0 rad/s`；YAML 可配置更低的值，但轮速不得超过源码中的 `5.0 rad/s` 项目上限，线速度和角速度需满足轮速及几何约束。前进与转向叠加超过轮速限制时，双轮同比缩放，保留运动曲率。SDK 未明确说明 wheel `Speed` 的单位或上限，当前驱动按 rad/s 换算；上述值是项目配置，并非厂商标称极限。真机验收需架空轮对比 `Speed_Actual` 与位置导数、测量有效滚动半径，并确认 `+vx` 前进、`+wz` 逆时针。wheel 保留在通用 `actuator_order`/`JointCommand` velocity 合同中，也可通过标准 `locomotion_command` 控制；两条路径共用实际 `LOW_LEVEL` 写入、锁和 watchdog。
