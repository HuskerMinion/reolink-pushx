# DNS redirect

Goal: make `pushx.reolink.com` resolve to the host running `pushx_listener.py`,
so the cameras' PIR motion POSTs land on it instead of Reolink's cloud. The
camera dials plain `http://pushx.reolink.com:80`, so a DNS override is all that's
needed — no TLS, no cert.

The override must live on **whatever resolver the cameras actually use** (handed
out by DHCP). Pick ONE option. Replace `<listener-ip>` with your host's LAN IP
(e.g. `192.168.1.10`).

## Option 1 — dnsmasq
```
# /etc/dnsmasq.d/pushx.conf
address=/pushx.reolink.com/<listener-ip>
```
```
sudo systemctl restart dnsmasq
```
Then point the cameras at this resolver (router DHCP "DNS server" = the dnsmasq
host). Cameras must re-DHCP (power cycle) to pick it up.

## Option 2 — Pi-hole
Local DNS → DNS Records:  `pushx.reolink.com -> <listener-ip>`
(or drop the same `address=/pushx.reolink.com/<listener-ip>` line in
`/etc/dnsmasq.d/`). No DHCP change if the cams already use Pi-hole.

## Option 3 — router host override
Many routers (OpenWrt / dd-wrt / Asus / etc.) have "static DNS" / "DNS host
entries": add `pushx.reolink.com -> <listener-ip>`. Simplest if the router is the
resolver.

## Verify
1. From a LAN host: `nslookup pushx.reolink.com` → must return `<listener-ip>`.
2. Run a camera on **battery** (so it truly sleeps/wakes), DNS pointed here.
3. Walk in front of it → a `POST /devices/<uid>/notifications` with the PIR
   alarm JSON appears in the listener log within a second or two.

## Notes / gotchas
- Port 80 needs root.
- `REAL_PUSHX_IP` in the listener is Cloudflare and may rotate; only matters for
  `--forward`.
- Redirecting `pushx` stops Reolink's own app push for these cams unless you run
  with `--forward`.
- Do this on a network you control; don't modify camera firmware.
