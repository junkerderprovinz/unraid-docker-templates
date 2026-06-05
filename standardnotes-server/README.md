# Standard Notes Server — Unraid template

Community Applications templates for a self-hosted [Standard Notes](https://standardnotes.com) backend.

- **[`standardnotes-server.xml`](standardnotes-server.xml)** — the Standard Notes sync server (needs an external MariaDB + Redis).
- **[`standardnotes-localstack.xml`](standardnotes-localstack.xml)** — S3-compatible file storage (LocalStack) for the server; it bootstraps the bucket via [`localstack_bootstrap.sh`](localstack_bootstrap.sh).

Setup help: [`docs/configuration.md`](docs/configuration.md), [`docs/sync-loop-troubleshooting.md`](docs/sync-loop-troubleshooting.md), and [`examples/.env.example`](examples/.env.example).

- **Install:** Unraid → **Apps** → search *Standard Notes*
- **Upstream:** <https://standardnotes.com>
- **Support:** <https://forums.unraid.net/topic/198819-support-junkerderprovinz-standard-notes-server/>
