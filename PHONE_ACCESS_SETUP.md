# Optoblock phone access

1. Start Optoblock and verify `http://127.0.0.1:8765` opens on the PC.
2. Install Tailscale on the PC and phone, and sign both into the same tailnet.
3. In Windows Administrator PowerShell run `tailscale serve --bg 8765`.
4. Open the HTTPS `.ts.net` URL printed by Tailscale on the phone.
5. Use the browser's **Add to Home Screen** action to install the PWA.

The Windows computer must remain powered on with Optoblock running. The API listens only on localhost; Tailscale Serve provides private HTTPS access. Do not use Funnel or open a public firewall port.

Check the proxy with `tailscale serve status`. Disable it with `tailscale serve reset`. Phone server startup can be disabled in Optoblock Settings; restart Optoblock after changing it.

Mobile V1 includes Today, tasks, a chronological planner, shopping, read-only projects, typed brain dumps, and text notes. It intentionally excludes database import/download, microphone activation, journal drawings, finance editing, dashboard layout, and Gmail actions. Live data is not cached as authoritative: when the PC cannot be reached, the PWA reports that Optoblock is offline.
