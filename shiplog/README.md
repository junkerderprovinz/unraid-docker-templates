# ShipLog — Unraid template

⚓ **ShipLog** is a read-only update advisor for your Docker host. Unraid already tells you *that*
an update is available and lets you apply it — ShipLog tells you **what actually changes** and
**how risky** it is first: the changelog between your running image and the newest one, a
deterministic risk verdict, and an optional AI summary. It never pulls, recreates, or stops
anything; the Docker socket is mounted **read-only**.

Full documentation, how-it-works and roadmap: **https://github.com/junkerderprovinz/shiplog**

## Install

Search **ShipLog** in the Unraid **Apps** tab, or add the template URL manually:

```
https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/shiplog/shiplog.xml
```

The only required mount is the Docker socket, **read-only**. Open the WebUI on port **8484**.

## Configuration

| Field | Variable / path | Default | Notes |
|---|---|---|---|
| WebUI Port | `8484` | `8484` | ShipLog web interface |
| Docker Socket | `/var/run/docker.sock` | `/var/run/docker.sock` | **read-only** (`ro`) — never written |
| Config | `/config` | `/mnt/user/appdata/shiplog` | SQLite db + curated-mapping override |
| Poll Interval | `POLL_INTERVAL` | `6h` | dropdown (1h/3h/6h/12h/24h) |
| GitHub Token | `GITHUB_TOKEN` | — | optional; raises the GitHub API limit for changelogs |
| Ollama URL / Model | `OLLAMA_URL` / `OLLAMA_MODEL` | — | optional AI changelog summaries |
| Matrix Homeserver / Token / Room | `MATRIX_*` | — | optional enriched notifications |
| Timezone | `TZ` | `Europe/Vienna` | dropdown (full IANA list) |

## Security

ShipLog only ever **reads** the Docker socket (mounted `:ro`) — it cannot start, stop, recreate,
or pull anything. v1 has no authentication and is intended for a trusted LAN; do not expose port
8484 to the internet. The info bubble inside Unraid's own Docker tab arrives via a companion
plugin (see the main repo's roadmap); this engine works today via its status page.
