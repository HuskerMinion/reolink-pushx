# reolink-pushx

**Get local motion events from Reolink battery cameras — no cloud, no hub, no firmware mods.**

Reolink battery cameras (Argus 2 and relatives) don't expose motion over the
usual local paths — the Baichuan idle motion push (`cmd 33`) never fires on an
idle connection, the HaCfg webhook (`cmd 806/807`) returns `400`, and the old
FCM cloud push is dead. So "records on motion / click to wake" against these
cams, locally, looks impossible.

It isn't. On a PIR trip the camera **wakes, and POSTs its alarm as plaintext
HTTP** to Reolink's push server:

```
POST /devices/<uid>/notifications HTTP/1.1
Host: pushx.reolink.com:80

{"secret":"<device-secret>","type":"alarm","alarm":{
  "message":"Alarms from <Camera>.","name":"PIR Motion Sensor","type":"RF",
  "device":"<Camera>","channel":1,"deviceModel":"Argus 2",
  "alarmTime":"2026-01-01T12:34:56.000-0700"}}
```

Point `pushx.reolink.com` at a box on your own LAN (one DNS override) and run the
tiny listener in this repo. Every motion event now lands on **your** server as a
plain POST you can forward into an NVR, Home Assistant, or anything else.

Because the camera is normally asleep and the **PIR is what wakes it**, that
wake-time POST *is* the motion signal — in the field, motion is the only thing
that boots the camera.

## Why this works (hardware/firmware context)

- SoC: **Grain Media GM8136** (ARM). The battery-cam firmware is **FreeRTOS**, a
  single monolithic image — **no Linux, no shell, no "root"**, and no way to run
  an on-camera agent. You don't need one: the stock firmware already detects PIR
  and pushes it out. You just redirect *where*.
- The push is **plaintext HTTP on port 80** to a hostname, so a LAN DNS override
  is all it takes — no TLS, no certificate, no camera changes.

## Quick start

1. **Run the listener** on a LAN host (port 80 needs root):
   ```
   sudo python3 pushx_listener.py --log /tmp/pushx.log
   ```
2. **Redirect DNS** so `pushx.reolink.com` resolves to that host. See
   [`docs/dns-redirect.md`](docs/dns-redirect.md) (dnsmasq / Pi-hole / router).
3. **Test:** run a camera on battery (so it truly sleeps/wakes), then walk in
   front of it. A `POST /devices/<uid>/notifications` with the PIR alarm JSON
   shows up in the log within a second or two.

Wire the `on_motion()` hook in `pushx_listener.py` into your own system. Pass
`--forward` to also relay to the real push server so the Reolink app keeps
working.

## Compatibility

| Model | Push to `pushx`? | Notes |
|------|------|------|
| Argus 2 | ✅ confirmed | GM8136 / FreeRTOS; plaintext HTTP :80 |
| Argus 3 Pro | ❓ help wanted | newer firmware; may use HTTPS / different host |
| Other battery cams | ❓ | please report via an issue |

If you confirm another model, open an issue/PR with the model, firmware line, and
whether the POST appears (redact your UID/secret/MAC).

## Security note

The motion push is **unauthenticated plaintext** and carries a per-device
`secret`. Anyone on the network path can read or spoof these alarms. Keep your
cameras on a trusted/VLAN'd network. This project is for intercepting **your own**
cameras on **your own** LAN — interoperability and local control, not attacking
anyone else's devices.

## Prior art / credits

- Baichuan protocol reverse engineering: the Neolink project.
- Reolink (Linux) camera flash-dump hacking: thirtythreeforty's write-ups.

## License

MIT — see [LICENSE](LICENSE).
