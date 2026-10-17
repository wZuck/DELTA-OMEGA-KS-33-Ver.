[English](README.md) | [简体中文](README.zh-CN.md)

# Rev5 PCB 脚本

这些脚本用于从 Rev4 直焊 PCB 重新生成 Rev5：

1. `build_ks33_rev5.py`：将全部 ULP 轴体替换为本地 KS-33 五脚封装，并为每键增加一只 SOD-323 二极管。
2. `route_ks33_rev5.py`：调用固定校验值的 Freerouting 2.5.0 JAR，导入布线后重新填充铜皮。
3. `fix_ks33_nets.py`：补齐自动布线无法完成的网络，并显式连接分裂的地铜皮岛。
4. `polish_ks33_rev5.py`：补宽受限走线、修正已知窄颈、统一封装与文字标注并删除冗余过孔。
5. `export_fab.sh`：重新生成 Gerber、钻孔、钻孔图和 ZIP。

Freerouting JAR SHA-256：

```text
f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7
```

示例：

```bash
KICAD_PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9
JAVA=/path/to/java
JAR=/path/to/freerouting-2.5.0.jar

"$KICAD_PY" pcb/scripts/build_ks33_rev5.py delta-omega-rev4-handsolder-left.kicad_pcb
"$KICAD_PY" pcb/scripts/route_ks33_rev5.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb \
  --java "$JAVA" --freerouting-jar "$JAR"
"$KICAD_PY" pcb/scripts/fix_ks33_nets.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb
"$KICAD_PY" pcb/scripts/polish_ks33_rev5.py \
  pcb/delta-omega-rev5-ks33-left.kicad_pcb
```

仓库内已提交的 PCB 与制造文件是最终依据。重新生成后必须再次运行各工程对应的 KiCad DRC；发布文件应保持 0 违规、0 未连接。

Freerouting 在相同输入下也可能生成电气等价但几何不同的走线。重新生成的板子应视为新候选版本，只有在 DRC 与 3D 渲染复检通过后才能替换已提交的发布文件。
