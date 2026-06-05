# Configuration Reference

Every variable the Unraid template exposes, with the same defaults as the
upstream [`.env.sample`](https://github.com/standardnotes/server/blob/main/.env.sample).

## Database

| Variable | Default | Notes |
|---|---|---|
| `DB_HOST` | *required* | IP address of your MariaDB container, e.g. `192.168.x.x`. |
| `DB_PORT` | `3306` | |
| `DB_USERNAME` | `std_notes_user` | |
| `DB_PASSWORD` | *required* | |
| `DB_DATABASE` | `standard_notes_db` | Must already exist; empty is fine. |
| `DB_TYPE` | `mysql` | **Internal driver value required for MariaDB.** Standard Notes / TypeORM uses the `mysql` driver string to talk to MariaDB. Do not change. |

### Provisioning the database

```sql
CREATE DATABASE IF NOT EXISTS standard_notes_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'std_notes_user'@'%' IDENTIFIED BY 'use-a-strong-password-here';
GRANT ALL PRIVILEGES ON standard_notes_db.* TO 'std_notes_user'@'%';
FLUSH PRIVILEGES;
```

Schema migrations run automatically on the first start of the
Standard Notes container.

## Cache

| Variable | Default | Notes |
|---|---|---|
| `REDIS_HOST` | *required* | IP address of your Redis container, e.g. `192.168.x.x`. |
| `REDIS_PORT` | `6379` | |
| `CACHE_TYPE` | `redis` | Leave at this value. |

A vanilla `redis:7-alpine` container with no auth is sufficient.

> 🔒 **Redis security.** This template does not expose a Redis
> password field. The official `standardnotes/server` image does not
> document a Redis-auth env var. Keep Redis isolated on a trusted
> VLAN / private bridge and firewall it off the public internet. Only
> add an auth env var if your specific image fork documents it.

## LocalStack (SNS / SQS)

LocalStack is the **required companion for the official Standard
Notes server image**. The worker process inside `standardnotes/server`
resolves the literal hostname `localstack` (default port `4566`) for
SNS / SQS. If that name does not resolve, the worker repeats
`SQSError: SQS receive message failed: getaddrinfo ENOTFOUND
localstack` in `/var/lib/server/logs/files-worker.log` and background
jobs fail in a loop, destabilising sync.

A files-only deployment can in theory skip the queue path, but the
upstream image still resolves `localstack` on startup. Even there,
worker logs must not show `ENOTFOUND localstack`.

The companion template `templates/standardnotes-localstack.xml` runs
`localstack/localstack:3.0` with `SERVICES=sns,sqs` and
`HOSTNAME_EXTERNAL=localstack`. The container name in the template is
`StandardNotes-LocalStack` for UI clarity; the server container must
resolve the bare name `localstack`. Working setups:

- **Same user-defined Docker network + alias `localstack`** (preferred).
  Docker's embedded DNS (`127.0.0.11`) resolves the alias.
- **Static IP / `br0` / macvlan**: Docker DNS is bypassed. Add
  `--add-host=localstack:<LocalStack-IP>` to `StandardNotes-Server`'s
  *Extra Parameters*.

Verify resolution from the server container:

```bash
docker exec StandardNotes-Server getent hosts localstack
docker exec StandardNotes-Server node -e "const net=require('net'); \
  const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
  s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
  s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
  s.on('error',e=>{console.error(e.message); process.exit(1)});"
```

The first line must print a non-empty result; the second must print
`LocalStack TCP connected`.

### Required bootstrap (SNS topics / SQS queues)

LocalStack starts **empty**. The official `standardnotes/server`
image expects a fixed set of SNS topics and SQS queues to exist
(`auth-local-queue`, `syncing-server-local-queue`,
`files-local-queue`, `revisions-server-local-queue`,
`analytics-local-queue`, `scheduler-local-queue`, and the matching
`*-local-topic` topics). Upstream's `docker-compose.example.yml`
mounts
[`docker/localstack_bootstrap.sh`](https://raw.githubusercontent.com/standardnotes/server/main/docker/localstack_bootstrap.sh)
into `/etc/localstack/init/ready.d/` so LocalStack runs it once on
startup.

This template ships the same script at
[`scripts/localstack_bootstrap.sh`](../scripts/localstack_bootstrap.sh)
and the LocalStack Unraid template exposes a **required** Path
mapping (*LocalStack Bootstrap Script*) at container target
`/etc/localstack/init/ready.d/localstack_bootstrap.sh`. Default host
path is `/mnt/user/appdata/standardnotes/localstack_bootstrap.sh`.

**Before** first start of the LocalStack container, place the
script on the host:

```bash
mkdir -p /mnt/user/appdata/standardnotes
curl -fsSL -o /mnt/user/appdata/standardnotes/localstack_bootstrap.sh \
  https://raw.githubusercontent.com/junkerderprovinz/standardnotes-server/main/scripts/localstack_bootstrap.sh
chmod +x /mnt/user/appdata/standardnotes/localstack_bootstrap.sh
```

Once LocalStack is running, verify the bootstrap created the
expected resources:

```bash
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sqs list-queues
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sns list-topics
```

Empty `Queues: []` / `Topics: []` means the init script never ran
(most often because the host file was missing on first start, or the
Path mapping was removed). Without these resources, TCP `4566` will
still connect, but `standardnotes/server` workers loop on missing
queues — account creation hangs and the first note can duplicate
infinitely. To fix in place on an already-running LocalStack, see
the *Emergency bootstrap* recipe in the
[main README](../README.md#emergency-bootstrap-localstack-already-running-no-queues).

## Secrets

All three are required and must be set to a 32-byte hex string. Generate
with `openssl rand -hex 32` (one invocation per variable).

| Variable | What it does | If you lose it |
|---|---|---|
| `AUTH_JWT_SECRET` | Signs auth tokens. | All sessions invalidated; users sign in again. |
| `AUTH_SERVER_ENCRYPTION_SERVER_KEY` | Encrypts data at rest, server-side. | **Permanent data loss** — back this up. |
| `VALET_TOKEN_SECRET` | Signs short-lived upload/download tokens for the files server. | New uploads/downloads fail until rotated; existing data unaffected. |

## Ports

| Container Port | Host Port | Purpose |
|---|---|---|
| `3000/tcp` | `3000` | API gateway. Put behind a reverse proxy. |
| `3104/tcp` | `3125` | Files server. Internal upstream files service listens on `3104` inside the container; `3125` is the published host port (per upstream `docker-compose.example.yml`). **Forward your reverse proxy to host port `3125`, not `3104`.** The Unraid template field *Files Server Port* uses `Target=3104` (container) with `Default=3125` (host). |

## Volumes

| Container Path | Suggested Host Path | Purpose |
|---|---|---|
| `/var/lib/server/logs` | `/mnt/user/appdata/standardnotes/logs` | Server logs. |
| `/opt/server/packages/files/dist/uploads` | `/mnt/user/appdata/standardnotes/uploads` | Encrypted file uploads. |

## Optional

| Variable | Default | Notes |
|---|---|---|
| `PUBLIC_FILES_SERVER_URL` | *(empty)* | **Full HTTPS URL** of the files server — *includes* `https://`. Example: `https://files.standardnotesserver.mydomain.tld`. Set only when you reverse-proxy the files server on its own hostname. |
| `COOKIE_DOMAIN` | *(empty)* | **Bare domain only** — *no* protocol, *no* `https://`, *no* trailing slash, *no* path. Example: `standardnotesserver.mydomain.tld`. Wrong: `https://standardnotesserver.mydomain.tld` (URL, not a domain). Must match the public host the reverse proxy serves over HTTPS. |

### `https://` placement — quick reference

| Setting | Where it lives | Value type | Includes `https://`? | Example |
|---|---|---|---|---|
| `COOKIE_DOMAIN` | Server env / Unraid template | Bare domain | **No** | `standardnotesserver.mydomain.tld` |
| `PUBLIC_FILES_SERVER_URL` | Server env / Unraid template | Full HTTPS URL | **Yes** | `https://files.standardnotesserver.mydomain.tld` |
| Custom Sync Server | Standard Notes client / web app UI | Full HTTPS URL | **Yes** | `https://standardnotesserver.mydomain.tld` |

A misplaced `https://` in `COOKIE_DOMAIN` is one of the most common
self-host pitfalls and has been linked to the duplicate-loop class of
bug. See [`docs/sync-loop-troubleshooting.md`](sync-loop-troubleshooting.md).

For anything beyond this — disabling user registration, custom SMTP,
extension server, payments — refer to the upstream
[`.env.sample`](https://github.com/standardnotes/server/blob/main/.env.sample)
and [self-hosting docs](https://standardnotes.com/help/self-hosting/getting-started).
Add the corresponding variables as **Variable** entries to the Unraid
template (Add another Path, Port, Variable, Label or Device).
