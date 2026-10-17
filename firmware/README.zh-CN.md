[English](README.md) | [简体中文](README.zh-CN.md)

# 固件说明

Rev5 PCB 矩阵已按以下 ZMK 仓库版本核对：

- `unspecworks/zmk-keyboard-delta-omega`
  `1df759db142469929841464905ec831ddb4e29b8`
- `unspecworks/zmk-delta-omega`
  `0f5392e87467c06d0d23c321b1728cc1539be950`
- `caksoylar/zmk-rgbled-widget`
  `e6b467792a1dabef8cfa5c9fd26bfefc9c16662b`

本目录是受控的 ZMK 配置快照，包含修正后的 keymap 和固定依赖的 [west 清单](config/west.yml)。上游配置依赖会移动的 `main` 分支，因此可复现构建必须使用本快照，而不是直接使用上游活动分支。

在本仓库之外建立独立 west workspace：

```bash
./firmware/scripts/setup_workspace.sh "$HOME/zmk-workspaces/delta-omega"
cd "$HOME/zmk-workspaces/delta-omega"
west build -s zmk/app -d build/left -b seeeduino_xiao_ble \
  -- -DZMK_CONFIG="$PWD/config" \
  -DSHIELD=delta_omega_left
```

`delta_omega_right` 和 `settings_reset` 使用相同方式构建。

## 矩阵

| 信号 | GPIO | 板级名称 |
|---|---|---|
| 第 1 行 | `P0.05` | `D5` |
| 第 2 行 | `P0.06` | `D6` |
| 第 3 行 | `P0.08` | `D8` |
| 第 4 行 | `P0.07` | `D7` |
| 左板第 1-5 列 | `P0.00`-`P0.04` | `D0`-`D4` |
| 右板第 6-10 列 | `P0.04`-`P0.00` | `D4`-`D0`，并设置列偏移 5 |

矩阵变换为 4 行 10 列。每颗轴体串联一只 SOD-323 二极管，焊盘 1 接行，焊盘 2 接轴体和列。因此 `diode-direction = "col2row"` 正确。

## 键位修复

核对发现上游右手组合键 `R_Gui_Alt` 错误使用了 `LG(LALT)`，应改为 `RG(RALT)`。当前受控配置已包含修复；[keymap.patch](zmk/keymap.patch) 作为上游审查补丁保留。

RGB LED 数据链为 `P0.10`（`D9`），与 PCB 一致。

## 构建状态

PCB、二极管方向、GPIO 和矩阵变换均已完成静态核对。当前仓库环境没有 west workspace 和 Zephyr 工具链，因此未执行完整 ZMK 编译。
