[English](GETTING_STARTED.md) | [简体中文](GETTING_STARTED.zh-CN.md)

# Getting Started

Please read this document carefully before beginning your build.
It may be long and tedious, but every section is written with only the most essential information in mind.

## Step 1: Choosing Your Switches

Rev5 uses **Gateron KS-33 Low Profile 3.0** switches with the five-pin MX
PCB layout.

The Rev5 footprint uses:

- Standard MX electrical-pin coordinates
- A 5.0 mm center hole
- 1.70 mm locator holes at ±5.08 mm
- Direct solder pins, not hot-swap sockets

Use the **3.0** generation specifically. Earlier Gateron KS-33 generations use
a different PCB pin layout and cannot be substituted on this board.

The original Rev4 files still support Cherry MX ULP or Kailh PG1316S for anyone
who wants to build the older design.

Reference: [Gateron KS-33 Low Profile 3.0](https://www.gateron.com/products/gateron-ks-33-low-profile-30-mechanical-switch)

## Keycaps

DELTA OMEGA KS-33 Ver. uses an **18 × 17 mm key pitch**. KS-33 3.0 has an
MX-compatible stem, but that does not mean every MX keycap will fit.

- Use compact low-profile MX keycaps whose bottom footprint stays clear at a
  17 mm row pitch.
- Test adjacent keycaps before final assembly. Standard 19.05 mm-spaced MX
  keycaps can collide between rows.
- Custom-printed low-profile MX keycaps are the most predictable option.

![Rev5 keycap fit envelope](./images/rev5_keycap_envelope.svg)

#### Height Considerations
The Rev5 case has a `15.2 mm`, `r1.8 mm` relief pocket at every switch and has
been checked against the KS-33 3.0 body. The keycap must stay within the
rounded envelope: `14 x 14 mm`, `r3.5 mm` below `z = 7.0 mm` and
`16.6 x 15.6 mm`, `r7.0 mm` above it. See the
[Rev5 mechanical notes](MECHANICAL.md) and supplied STEP fit envelope.

The Rev5 outer rim is raised to `z = 8.8 mm`, nearly level with the
`z = 9.0 mm` keycap envelope top. This gives the intended enclosed typing feel
while preserving the internal opening and mounting geometry.

## Soldering

The KS-33 3.0 switch pins and the separate 1N4148WS diodes are designed for
manual soldering. A hot plate or reflow process is not required.

1. Solder the SOD-323 diodes before installing the switches.
2. Dry-fit each switch. All five posts must enter without force.
3. Solder the two electrical pins from the back of the PCB.
4. Do not fill the center or locator holes with solder.
5. Trim the electrical pins to no more than 0.5 mm below the PCB and insulate
   any exposed metal before fitting the bottom cover.

## PCB

### Main PCB
The PCB is **non-reversible** — you will need a left and right pair.

Two ordering options:
1. A single Gerber including both left and right PCBs
2. Separate left and right PCB files

**Why?**
Ordering both together requires mouse-bites or V-cuts to split, leaving rough edges. Since DELTA OMEGA KS-33 Ver. leaves the bottom PCB exposed, rough edges and tight tolerances can cause issues.

Cost difference is negligible (1~2 USD), so choose based on preference.

### PCB Thickness

![PCB Stack](./images/pcb_stack.png)

For Rev5:
- Use a **1.6 mm main PCB**. The KS-33 locator pegs are 1.2 mm long and the
  electrical pins are 3.0 mm long.
- Use an optional 0.8 mm PCB bottom cover if that construction is desired.

The older Rev4 0.8 mm main-PCB stack is not recommended for Rev5.

> [!TIP]
> The cover can be countersunk for a flat bottom. Note that 0.8mm is too thin for a perfect countersink, and the lower right corner (on the left half) is especially challenging.

> [!TIP]
> Customize your cover with some designs.

## Case

The case is recommended to be **CNC aluminum**.
Due to the thin and portability focus, a rigid case material ensures durability.

### Cost
CNC machining is often the largest concern.

- With JLC CNC (Aluminum A6061, bead blasting + anodizing):
  Approx. **32 USD per side**
- Prices may vary, and should only be considered a rough reference

> [!TIP]
> Ordering multiple units (e.g., with friends) significantly reduces cost — as low as 30 USD per side. Coupons and alternative CNC shops can further reduce expenses.

Combined PCB + CNC costs are generally around **80–100 USD (excluding shipping/tax)**.

### Magnets
Three magnets can be installed inside the case to allow the halves to snap together for portability.

- This is optional; if you’re concerned about scratches, consider alternative storage solutions.
- Refer to the BOM for recommended magnet specifications (tested values).

### CNC Experience with JLC

For prototyping, I placed around six CNC orders from JLCCNC. Overall, the quality was acceptable: some uneven chamfering and minor surface scratches (barely noticeable) were present. But one piece arrived slightly warped(deformation), which is understandable given the hollow structure and thin sidewalls. so it carries an inherent risk of deformation. In my case, about 0.3 mm of tolerance shift occurred, requiring some manual adjustment with hand tools.

If you encounter similar issues, it would be a good idea to discuss them directly with JLC and work out possible solutions.

## LED Indicator

![LED Indicator](./images/led_indicator.png)

The design utilizes three individual LEDs as an indirect glow indicator. The color may be chosen according to user preference; however, the default configuration is Red, Green, and Blue. Refer to the [zmk-rgbled-widget](https://github.com/caksoylar/zmk-rgbled-widget) documentation to adjust the settings according to your preference.

When operating LEDs at 3.3 V, it is recommended to install appropriate resistors. Using resistors with lower resistance values will increase brightness, but also result in higher battery consumption and, to a lesser extent, greater load on the MCU. Note that even when identical resistor values are used, brightness may vary by LED color. Consider these factors when selecting resistor values. If uncertain, a 220Ω resistor is generally a safe and effective choice.

## Battery

You can use a 3.7V Li-Po battery. The size must fit within **25.2 mm × 17.7 mm × 4.2 mm**.
However, the commonly available **401725** model may not fit properly. This is because typical specifications often exclude the size of the protection circuit, and lithium polymer batteries tend to have significant packaging tolerances.

Be sure to check the actual dimensions before purchasing. Do not force the battery into place.


---


## Next Steps

- [Bill of Materials](./BOM.md)
- [Build Guides](./BUILD_GUIDES.md)
