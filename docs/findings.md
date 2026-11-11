# Findings — Reolink Argus 2 (GM8136) battery camera

## SoC / firmware
- **SoC:** Grain Media **GM8136** (ARM). Boot banner reports the GM8135S/GM8136
  family; `flash signature = GM8136`.
- **OS:** **FreeRTOS**, not Linux. One monolithic RTOS application image
  (`libplatform ...[GM8136S_FREERTOS]`). Bootloader is Grain Media's
  `MP SPI-NOR Bootstrap` — **not U-Boot**. Consequence: **no shell, no login, no
  users, no "root," no way to drop in an on-camera agent.** The serial console is
  diagnostic output only.
- **Sensor:** Sony IMX291/IMX307, 1080p.

## Flash layout (SPI-NOR, 16 MB)
- NOR chip id `c2 20 18` (Macronix MX25L128, 16 MB).
- Partition 0: `0x400000–0x700000`, **read-only** (application image).
- Partition 1: `0xD90000–0xFBE800`, **writable** (config / static params).
- Dual-image with magic check (`Invalid magic -> Run factory app`), so a bad
  patch falls back or bricks. Externally reflashable (SOIC-8 clip + flashrom) if
  you dump first.

## The motion push (the useful part)
On a PIR trip the camera wakes, resolves `pushx.reolink.com`, connects to **port
80**, and sends:

```
POST /devices/<uid>/notifications HTTP/1.1
Host: pushx.reolink.com:80
Content-Length: 240

{"secret":"<device-secret>","type":"alarm","alarm":{
  "message":"Alarms from <Camera>.","name":"PIR Motion Sensor","type":"RF",
  "device":"<Camera>","sound":"default","channel":1,"deviceModel":"Argus 2",
  "alarmTime":"2026-01-01T12:34:56.000-0700"}}
```

Server replies:
```
HTTP/1.1 200 OK
{"status":{"code":0,"detail":"OK"},"data":{"sent":0}}
```

Notes:
- Plaintext HTTP, so a LAN DNS override is enough to capture it.
- `alarmTime` advances with real time (RTC-backed) → freshly generated per wake,
  not a cached replay.
- The camera is normally asleep; the **PIR wakes it**, so the wake-time POST *is*
  the motion event.

## Other cloud endpoints it contacts

For a fully cloud-free setup you may also want to block these (they are for
remote app access via the camera's UID and are **not** needed for local motion
or for a local Baichuan client that uses UDP discovery):

- `p2p.reolink.com:9999` — P2P rendezvous / signaling.
- a "manager" server (seen by IP) and a register/heartbeat/peer server
  (`...:58200`) — the P2P relay for out-of-LAN access.

Redirecting only `pushx.reolink.com` leaves these untouched, which is usually
what you want (motion works locally; remote app access still functions).

## What does NOT work (for reference)
- **Baichuan `cmd 33` idle push:** subscription is acked (`200`) but the camera
  pushes zero events on an idle connection — it's a mains-camera mechanism.
- **HaCfg webhook (`cmd 806/807`):** returns `400` on Argus 2 firmware (`405` on
  Argus 3 Pro). Not supported.
- **FCM cloud push:** API discontinued.

The `pushx` HTTP push is the path that actually fires.

## UART
See [`uart-recon.md`](uart-recon.md). Getting the serial console is how the push
mechanism was discovered, but it is **not needed** to use this project.
