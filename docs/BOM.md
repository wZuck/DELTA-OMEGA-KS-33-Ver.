[English](BOM.md) | [简体中文](BOM.zh-CN.md)

# Bill of Materials

| Component        | Specification                                              | Quantity | Notes  |
|------------------|------------------------------------------------------------|----------|--------|
| MCU Controller   | SeeedStudio XIAO nRF52840                                  | 2        |        |
| LP MX Switches   | Gateron KS-33 Low Profile 3.0 five-pin; reference `KS-33BS10B043NW-Y92B` | 34 | Direct solder, not hot-swap; verify the 3.0 PCB drawing |
| LP MX Keycaps    | MX stem; rounded fit envelope: 14×14 r3.5 below z=7, 16.6×15.6 r7 above | 34 | Case rim is z=8.8; see mechanical notes |
| Power Switches   | MK-12C02                                                   | 2        |        |
| Reset Switches   | EVQ-PUL02K                                                 | 2        | Compatible with EVQ-PU[A\|C\|J\|L]02K |
| Diodes           | SOD-323                                                    | 34       | 1N4148WS |
| Batteries        | 3.7 V LiPo                                                 | 2        | Maximum size: 25.2 mm × 17.7 mm × 4.2 mm |
| Screws           | M2 × 3 mm                                                  | 10       | If countersink is not used, choose ultra-low head screws (ex. 0.8 mm) |
| LEDs             | 0805 (2012 Metric)                                         | 6        | Optional |
| LED Resistors    | 1206 (3216 Metric) 220Ω ~ 470Ω                             | 6        | Optional |
| Magnets          | Rounded, OD 8 mm, 3 mm thickness, minimum N52 grade        | 6        | Optional |
| ESD Protection Capacitor | 1206 (3216 Metric) 1nF 50V [C0G\|NP0\|X7R]           | 2        | Optional |
| ESD Protection Resistor | 1206 (3216 Metric) 1MΩ                              | 2        | Optional |

## Next Steps

- [Build Guides](./BUILD_GUIDES.md)
