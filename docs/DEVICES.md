# Devices

The server is just Python + a web page. Run it wherever you like, open the URL.

## Your computer (Mac / Windows / Linux)

```bash
pip install -r requirements.txt
cp .env.example .env   # add your key
python server.py
```
Open http://localhost:8000.

## Docker (any machine, always-on)

```bash
docker compose up --build -d
```
Restarts automatically. Workspace, memory, and spend data persist in
`./workspace`, `./memory`, `./data`.

## iPhone

iOS can't run a Python server persistently, so host it somewhere and use the web UI:

1. Run the server on your computer, a Raspberry Pi, or a VPS.
2. On iPhone Safari open `http://<host>:8000`.
3. **Share → Add to Home Screen** — it behaves like an app.

For access outside your home network without exposing ports, put the server behind
[Tailscale](https://tailscale.com) (free for personal use) and open the Tailscale IP
on your phone. Do **not** port-forward it to the public internet as-is — v1 has no
login screen.

## Android

Option A: same as iPhone — host it elsewhere, use the web UI.
Option B: run it on-device with Termux:

```bash
pkg install python
pip install -r requirements.txt
python server.py
```
Then open http://localhost:8000 in Chrome.

## Raspberry Pi (the $0/month always-on agent)

A Pi 4/5 sipping power on your shelf runs this 24/7 for roughly $5–10/year in
electricity. Docker install, Tailscale for phone access, done.

## Free cloud hosts

Render, Fly.io, and Hugging Face Spaces all have free tiers that run this. Set the
`.env` values as the host's environment variables/secrets. Note: free tiers sleep —
first message of the day wakes it up.

## Security notes

- Tools are jailed to `workspace/` and destructive command patterns are blocked, but
  the agent **can run shell commands** — treat the host as yours alone.
- Keep the port on your LAN or behind Tailscale/WireGuard. If you must expose it,
  put a reverse proxy with basic auth (Caddy/Nginx) in front.
- API keys live in `.env`, which is git-ignored and never committed.
