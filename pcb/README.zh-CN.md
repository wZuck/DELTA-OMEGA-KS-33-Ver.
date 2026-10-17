[English](README.md) | [简体中文](README.zh-CN.md)

# PCB

> [!TIP]
> 如果这是你第一次接触本项目，请先阅读[入门指南](./../docs/GETTING_STARTED.zh-CN.md)。

---

## PCB 文件列表

| 文件 | 说明 | 备注 |
|---|---|---|
| `delta-omega-rev5-ks33-left` | Rev5 左板，Gateron KS-33 LP 3.0 五脚 | 当前版本 |
| `delta-omega-rev5-ks33-right` | Rev5 右板，Gateron KS-33 LP 3.0 五脚 | 当前版本 |
| `delta-omega-rev5-ks33-both` | Rev5 左右拼板，带邮票孔连接 | 使用前确认拼板分离方式 |
| `delta-omega-rev4-handsolder-both` | 原始 ULP 左右拼板 | 旧版，未测试拼板分离 |
| `delta-omega-rev4-handsolder-left` | 原始 ULP 左板 | 旧版 |
| `delta-omega-rev4-handsolder-right` | 原始 ULP 右板 | 旧版 |
| `delta_omega_bottom_cover` | PCB 底盖 | 可翻转使用 |
| `delta-omega-rev4-smd-both` | 原始 ULP SMD 版本 | 旧版，未测试 |

![Rev5 KS-33 左板](./../docs/images/rev5_ks33_left.png)

![Rev5 KS-33 拼板](./../docs/images/rev5_ks33_both.png)

Rev5 使用自定义 `Gateron_KS33_LP_3.0_5Pin` 封装：

- 标准 MX 电气脚位置
- 5.0 mm 中心孔
- 位于 ±5.08 mm 的 1.70 mm 定位孔
- 轴体外侧独立 SOD-323 二极管位置

## Rev5 验证

- 左板、右板和拼板 KiCad DRC 均为 0 违规、0 未连接
- 共 34 个轴体和 34 只 SOD-323 二极管
- 双层 1.6 mm PCB，信号线最小宽度 0.2 mm
- 除 XIAO 邮票孔区域外，铜到板边间距为 0.2 mm
- XIAO 边缘焊盘例外仅通过工程内 `.kicad_dru` 规则生效
- 分裂的地铜皮岛已使用显式走线连接
- Gerber、钻孔、钻孔图和 ZIP 均已由当前 Rev5 PCB 重新生成

本工程没有 KiCad 原理图，因此验证范围是 PCB 连通性、矩阵映射、二极管方向、铜皮规则和制造文件，不包含原理图与 PCB 一致性检查。

---

## 如何下单

本指南以 **[JLCPCB](https://jlcpcb.com)** 为例。其他 PCB 厂商的流程略有不同，但整体步骤基本一致。

下单时上传 [./gerbers/](./gerbers/) 中对应的 ZIP 文件。当前轴体方案请使用 `rev5-ks33` 对应的 Gerber 包。

---

### 推荐参数

| 参数 | 推荐值 | 说明 |
|---|---|---|
| 基材 | FR-4 | 标准 PCB 基材 |
| 层数 | 2 | 双面板 |
| PCB 数量 | 按需 | |
| 产品类型 | Industrial / Consumer Electronics | |
| 不同设计数 | 1 | 如果上传左右拼板 Gerber，请选择 **2**。[^1] |
| PCB 厚度 | 1.6 mm | KS-33 定位柱长 1.2 mm、电气脚长 3.0 mm，Rev5 固定使用 1.6 mm |
| PCB 颜色 | 自选 | |
| 表面处理 | 自选 | |
| Mark on PCB | Remove Mark | 建议移除，以获得更干净的成品 |

[^1]: 如果未选择正确数量，JLCPCB 通常会人工审核订单并引导修正。
