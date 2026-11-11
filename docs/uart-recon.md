# UART recon — Argus 2 (GM8136)

Getting the serial console is how the `pushx` motion push was discovered. You do
**not** need it to use this project — it's here for anyone reverse engineering
further. There is no shell to reach (the firmware is FreeRTOS); the console is
diagnostic output.

## The header
- Back board, by the **`8136UART`** silkscreen. Later board revs ship the
  footprint **unpopulated** — you solder to the pads.
- **4-pin inline** row. Pin 1 is marked by a silkscreen triangle/arrow; pin 4 is
  the far end.
- Observed mapping (confirm on your unit — see below):

  | Pin | Function |
  |----|----|
  | 1 (arrow) | VCC ~3.3 V |
  | 2 | TX (camera out) |
  | 3 | RX (camera in) |
  | 4 (far) | GND |

- Large square pads flanking the row are also GND (connector shell) — easy,
  sturdy solder points for the ground lead.

## Settings
- **3.3 V logic** (GM8136 I/O is 3.3 V — never 5 V).
- **115200 8-N-1**, no flow control. Console is `ttyS0`-equivalent at 115200.

## Procedure (read-only first)
1. Set your USB-TTL adapter to **3.3 V** and verify (VCC pin ≈ 3.3 V, not 5 V).
2. Solder **GND** (a big square pad) → adapter GND, and **pin 2** → adapter RX.
   Leave VCC (pin 1) and pin 3 disconnected.
3. Open a terminal at 115200 8-N-1 and power the camera (connect battery).
4. If you get boot text, pin 2 was TX. If it's silent, move the RX wire to
   pin 3. Garbage = wrong baud.
5. Only add adapter TX → camera RX later if you want to type (there's no shell,
   so there's little reason to).

## What the boot log shows
- Grain Media SPI-NOR bootstrap → FreeRTOS app (no U-Boot prompt, no login).
- SoC/flash details (see [`findings.md`](findings.md)).
- On a PIR wake, the plaintext HTTP POST to `pushx.reolink.com` — the motion
  signal this project intercepts.

> Redact your own `secret`, `uid`, `MAC`, `P2Pkey` and any network details before
> sharing a boot log.
