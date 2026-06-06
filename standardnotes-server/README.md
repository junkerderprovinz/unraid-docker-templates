<h1 align="center">Standard Notes Server for Unraid</h1>

<a href="https://standardnotes.com">
  <img src="assets/banner.svg" alt="Standard Notes Server for Unraid" width="100%">
</a>

<p align="center">
  <a href="https://github.com/junkerderprovinz/unraid-docker-templates/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/junkerderprovinz/unraid-docker-templates/validate.yml?branch=main&label=Validate&style=for-the-badge&logo=githubactions&logoColor=white" alt="Validate" height="36"></a>&nbsp;
  <a href="https://hub.docker.com/r/standardnotes/server"><img src="https://img.shields.io/badge/Docker-standardnotes%2Fserver-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker image" height="36"></a>&nbsp;
  <a href="https://standardnotes.com"><img src="https://img.shields.io/badge/Standard%20Notes-self--hosted-086DD7?style=for-the-badge&logo=standardnotes&logoColor=white" alt="Standard Notes" height="36"></a>&nbsp;
  <a href="#5-database--cache"><img src="https://img.shields.io/badge/Database-MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white" alt="MariaDB" height="36"></a>&nbsp;
  <a href="#5-database--cache"><img src="https://img.shields.io/badge/Cache-Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" height="36"></a>&nbsp;
  <a href="#3-quick-start-on-unraid"><img src="https://img.shields.io/badge/Unraid-Community%20Template-f15a2c?style=for-the-badge&logo=unraid&logoColor=white" alt="Unraid Community Template" height="36"></a>&nbsp;
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License: MIT" height="36"></a>
</p>

<p align="center">
A clean, opinionated <b>Unraid Community Template</b> for the
<a href="https://standardnotes.com">Standard Notes</a> self-hosted backend.
Run your own end-to-end-encrypted notes server on Unraid in a few minutes,
with <b>MariaDB</b> and <b>Redis</b> as separate, reusable containers — no
bundled databases, no surprises.
</p>

<p align="center">
<i>Unofficial community wrapper. Not affiliated with or supported by Standard Notes.</i>
</p>

<br>

<p align="center">
  <a href="https://buymeacoffee.com/junkerderprovinz">
    <img src="assets/button-buy-me-a-coffee.svg" alt="Buy me a coffee" width="220">
  </a>
</p>

<br>

## Table of Contents

0. [⚠️ Sync-Loop / Duplicate Notes Guardrails](#0-sync-loop--duplicate-notes-guardrails)
1. [What is this?](#1-what-is-this)
2. [Architecture](#2-architecture)
3. [Quick Start on Unraid](#3-quick-start-on-unraid)
4. [Generating Secrets](#4-generating-secrets)
5. [Database & Cache](#5-database--cache)
6. [Configuration Reference](#6-configuration-reference)
7. [Security](#7-security)
8. [Reverse Proxy](#8-reverse-proxy)
9. [Backup & Restore](#9-backup--restore)
10. [Updating](#10-updating)
11. [Troubleshooting](#11-troubleshooting)
12. [Contributing / License](#12-contributing--license)
13. [Support this project](#13-support-this-project)

<br>

## 0. Sync-Loop / Duplicate Notes Guardrails

> ⚠️ **Read this before you connect a real Standard Notes account.**
> Diese Sektion bitte vor der ersten Anmeldung lesen.

Self-hosted Standard Notes installations — including this Unraid
template — can in rare configurations produce **massive note
duplication**: a single new note replicates dozens or hundreds of
times within seconds in the client. This is almost always a
**configuration** problem in the surrounding stack (sync, cookies,
proxy, cache), **not** a bug in your notes themselves. Once it starts,
every additional client write makes the situation worse.

### Common causes (Unraid / self-hosted)

- **Sync conflicts** between clients. Standard Notes' [official
  duplicate-handling docs](https://standardnotes.com/help/33/how-do-i-clear-duplicates)
  state that the **server cannot decrypt or merge note content** — when
  two clients sync conflicting versions of the same note, the app
  duplicates the conflicting copy on the client side. With several
  clients online and an unstable backend, the cascade can run away.
- **Redis unreachable or wrong host/port.** If `REDIS_HOST` /
  `REDIS_PORT` are wrong, the server logs `ECONNREFUSED` (or the
  connection times out) and sync state is not deduplicated correctly
  across requests. A *timeout* (not refusal) usually means a firewall
  / VLAN / `br0` routing problem rather than a wrong port.
- **LocalStack missing or unresolvable.** The official
  `standardnotes/server` image expects to resolve the hostname
  `localstack` (default port `4566`) for SNS / SQS. If the worker
  cannot resolve it, `/var/lib/server/logs/files-worker.log` fills
  with `SQSError: SQS receive message failed: getaddrinfo ENOTFOUND
  localstack` and background jobs fail in a loop. This destabilises
  the worker pipeline and is a known precursor to sync / duplication
  problems — LocalStack is **not** optional in practice, see
  [§ 2](#2-architecture).
- **LocalStack reachable but uninitialised (no topics / queues).**
  Even when `localstack:4566` is connectable, LocalStack starts
  **empty**. The official `standardnotes/server` image expects a
  fixed set of SNS topics and SQS queues (`auth-local-queue`,
  `syncing-server-local-queue`, `files-local-queue`,
  `revisions-server-local-queue`, …). Upstream's
  `docker-compose.example.yml` mounts
  [`docker/localstack_bootstrap.sh`](https://raw.githubusercontent.com/standardnotes/server/main/docker/localstack_bootstrap.sh)
  into `/etc/localstack/init/ready.d/` to create them. This template
  ships the same script at
  [`scripts/localstack_bootstrap.sh`](scripts/localstack_bootstrap.sh)
  and the LocalStack template has a **required** *LocalStack
  Bootstrap Script* Path mapping. **Symptoms when missing:** TCP
  4566 connects fine and `getent hosts localstack` returns an IP,
  but **account creation hangs** and the **first note duplicates
  infinitely** because the workers loop on missing queues. Confirm
  with:
  ```bash
  docker exec StandardNotes-LocalStack \
    awslocal --endpoint-url=http://localhost:4566 sqs list-queues
  docker exec StandardNotes-LocalStack \
    awslocal --endpoint-url=http://localhost:4566 sns list-topics
  ```
  Both must list the `*-local-queue` / `*-local-topic` entries. An
  empty `Queues: []` / `Topics: []` means the bootstrap script did
  not run — see [Step 2 of the Quick Start](#step-2--start-localstack-required-companion).
- **Bad `COOKIE_DOMAIN` / session-cookie handling behind a reverse
  proxy.** Symptoms include `No cookies provided for cookie-based
  session token` in the server log and a `/v1/items` request loop.
  See the upstream forum
  [issue #3635](https://github.com/standardnotes/forum/issues/3635).
- **Reverse proxy serving the API over HTTP instead of HTTPS.** Modern
  clients require HTTPS; without it, `Secure` cookies are dropped and
  the session loop above can trigger.
- **Wrong host or unreachable network** for `DB_HOST` / `REDIS_HOST`.
  This template asks for IP addresses (e.g. `192.168.x.x`) — they
  are unambiguous across Unraid's bridge / `br0` / VLAN setups. Make
  sure the IP is static (DHCP reservation or fixed) so it does not
  change on container restart.
- **Image / client version mismatch.** The legacy
  [`standardnotes/syncing-server` issue
  #102](https://github.com/standardnotes/syncing-server/issues/102)
  documents how mixing a stable web app with a development
  syncing-server caused `Syncing: 0/1` and duplicate cascades. That
  repo is **archived and historical** — the current image is
  `standardnotes/server` — but the same class of mismatch can still
  happen if you pin to a broken `latest`.

### `https://` — where it belongs and where it does NOT

A misplaced `https://` in `COOKIE_DOMAIN` is one of the most common
self-host pitfalls and has been observed to cause the duplicate-loop
class of bug. Use this matrix:

| Field | Value type | Includes `https://`? | Example |
|---|---|---|---|
| `COOKIE_DOMAIN` (env / template) | **Bare domain only** | ❌ **No** | `standardnotesserver.mydomain.tld` |
| `PUBLIC_FILES_SERVER_URL` (env / template) | **Full HTTPS URL** | ✅ **Yes** | `https://files.standardnotesserver.mydomain.tld` |
| Custom Sync Server (in client / web app) | **Full HTTPS URL** | ✅ **Yes** | `https://standardnotesserver.mydomain.tld` |

If you accidentally set `COOKIE_DOMAIN=https://standardnotesserver.mydomain.tld`,
the server emits cookies for the literal string `https://...` which no
browser will accept — sessions silently break, the client retries
`/v1/items`, and conflict-resolution on the client can cascade into
duplicates.

### Emergency checklist — duplicates happening RIGHT NOW

> Stop first. Diagnose second. Edit nothing.

1. **Stop every connected client immediately.** Sign out (don't just
   close) on web UI, desktop, mobile. Background sync keeps fanning the
   loop out otherwise.
2. **Stop the StandardNotes-Server container.** Unraid → Docker → stop.
   Leave MariaDB, Redis and LocalStack running so you can inspect
   state.
3. **Do NOT reconnect any existing client.** Especially not your
   long-history account. Each new edit during a loop can spawn more
   duplicates.
4. **Verify Redis is reachable from StandardNotes-Server.**
   The authoritative test runs from **inside** the
   `StandardNotes-Server` container, using the actual Redis IP — that
   is the network namespace the server itself talks to Redis from:

    ```bash
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(6379,'192.168.x.x'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('Redis TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('Redis TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    Replace `192.168.x.x` with your Redis container IP. Expected:
    `Redis TCP connected`. A timeout means a firewall / VLAN / `br0`
    routing problem between the server container's network and the
    Redis host — fix it before anything else. Tail the server log for
    `ECONNREFUSED` / connection-timeout lines against that host.

    > 📌 You already run an **official Redis container** for the
    > sync cache — there is no second Redis server to install. If you
    > also want a quick CLI ping with `redis-cli`, the
    > `redis:7-alpine` image can be launched as a **disposable client
    > container** (no persistent state, no second Redis server):
    >
    > ```bash
    > docker run --rm --network <same-network-as-redis> \
    >   redis:7-alpine redis-cli -h 192.168.x.x -p 6379 ping
    > ```
    >
    > On `br0` / macvlan / VLAN / static-IP setups the default
    > `docker run` lands on the **default bridge**, which usually
    > **cannot route** to a VLAN container — so `--rm redis:7-alpine
    > redis-cli ping` will time out even when Redis is healthy. Pass
    > `--network` (or `--ip` on the same `br0` / macvlan network as
    > Redis), or skip this client test entirely and trust the
    > in-container `node -e` probe above as the source of truth.
5. **Verify LocalStack is running and resolvable as `localstack`.**
   The worker resolves the literal hostname `localstack` for SNS /
   SQS, so DNS *and* TCP both have to work:

    ```bash
    docker exec StandardNotes-Server getent hosts localstack
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    The first command must print a non-empty line. If it is empty,
    Docker DNS cannot resolve `localstack` from the server container —
    see the static-IP / `br0` / macvlan note below. Tail
    `/var/lib/server/logs/files-worker.log` for `SQSError: SQS receive
    message failed: getaddrinfo ENOTFOUND localstack`; if you see it,
    fix LocalStack reachability *before* reconnecting any client.

    Then — **TCP-reachable is not enough**. LocalStack starts empty;
    the official `standardnotes/server` workers expect a fixed set of
    SNS topics and SQS queues to already exist. Verify they do:

    ```bash
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sqs list-queues
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sns list-topics
    ```

    Both must list the `*-local-queue` / `*-local-topic` entries
    (`auth-local-queue`, `syncing-server-local-queue`,
    `files-local-queue`, `revisions-server-local-queue`,
    `analytics-local-queue`, `scheduler-local-queue` and the matching
    topics). An empty `Queues: []` / `Topics: []` means the bootstrap
    script never ran — see *Emergency bootstrap (LocalStack already
    running, no queues)* below.

    > 📌 **Static IP / `br0` / macvlan / VLAN.** Docker's built-in
    > DNS (`127.0.0.11`) only resolves container names when both
    > containers share a **user-defined Docker network**. Containers
    > assigned a static IP on `br0` / macvlan / `br0.<vlan>` bypass
    > that DNS server and will *not* resolve `localstack`. Two
    > working options:
    >
    > - Put StandardNotes-Server and StandardNotes-LocalStack on the
    >   **same user-defined Docker network** (e.g. a custom bridge),
    >   and either name the LocalStack container `localstack` or give
    >   it a network alias `localstack`.
    > - Or, keep `br0` / macvlan / VLAN: install
    >   `StandardNotes-LocalStack` on the **same VLAN** as
    >   StandardNotes-Server with a **fixed IP** (e.g. `192.168.x.x`),
    >   then **append** `--add-host=localstack:<LocalStack-IP>` to
    >   StandardNotes-Server's *Extra Parameters* and restart it.
    >   `getent hosts localstack` must then return that IP.
6. **Check `COOKIE_DOMAIN`.** Verify it is a **bare domain** —
   `standardnotesserver.mydomain.tld`, not `https://...`, not a URL,
   no trailing slash. Verify the Custom Sync Server URL in the client
   is the **full HTTPS URL** `https://standardnotesserver.mydomain.tld`.
7. **If the test/throwaway account is the one that duplicated:**
   delete it (or drop and recreate the database / wipe the test
   account) before bringing the server back up. Carrying a
   already-corrupted account into a "fixed" deployment will reproduce
   the cascade as soon as a client reconnects.

Full triage: [`docs/sync-loop-troubleshooting.md`](docs/sync-loop-troubleshooting.md).

### Emergency bootstrap (LocalStack already running, no queues)

If LocalStack is up and TCP-reachable but `sqs list-queues` /
`sns list-topics` come back **empty**, the init script was never
mounted (template was deployed before this fix, or the host file was
missing on first start). LocalStack's `init/ready.d/` hook only fires
**once**, so just restarting the container after fixing the mount is
the long-term fix — but you can also bootstrap an already-running
LocalStack in place, without recreating it:

```bash
# 1. Pull the script onto the Unraid host
curl -fsSL -o /tmp/localstack_bootstrap.sh \
  https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/scripts/localstack_bootstrap.sh

# 2. Copy it into the running LocalStack container
docker cp /tmp/localstack_bootstrap.sh \
  StandardNotes-LocalStack:/tmp/localstack_bootstrap.sh

# 3. Run it in-place. `awslocal` is preinstalled in the LocalStack image.
docker exec StandardNotes-LocalStack \
  bash /tmp/localstack_bootstrap.sh

# 4. Verify
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sqs list-queues
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sns list-topics
```

After this, **also** persist the fix for next time:

1. Place the script at the host path the LocalStack template's
   *LocalStack Bootstrap Script* Path mapping points at — by default
   `/mnt/user/appdata/standardnotes/localstack_bootstrap.sh` — and
   `chmod +x` it. See
   [Step 2 of the Quick Start](#step-2--start-localstack-required-companion)
   for the one-liner.
2. Restart `StandardNotes-Server` so its workers reconnect against the
   now-populated SNS / SQS.

### Hard guardrails before you migrate any real notes

1. **Test with a fresh, throwaway account first.** Do **not** point
   your existing client (with months of real notes) at this server
   until you have verified end-to-end sync with a brand-new account.
2. **Use one client at a time** during the test. Connect a second
   device only once a single note has round-tripped cleanly.
3. **Make a decrypted backup / export** of your real notes from
   `standardnotes.com` (or your existing self-hosted server) **before**
   reconnecting any existing client.
4. **If duplication starts: stop.** Stop all clients, stop the server
   container, inspect logs and database. Do **not** keep editing —
   each edit can fan out further.

Full step-by-step checklist:
[`docs/sync-loop-troubleshooting.md`](docs/sync-loop-troubleshooting.md).

### Known risk — official + historical context

- **Official:** Standard Notes' help article *How do I clear
  duplicates?* states that duplicates are an **app-side conflict
  resolution** mechanism. The server cannot decrypt note bodies, so
  it cannot merge conflicts; the client duplicates conflicting copies
  to avoid silent data loss.
  <https://standardnotes.com/help/33/how-do-i-clear-duplicates>
- **Historical / legacy:** The old archived
  [`standardnotes/syncing-server`](https://github.com/standardnotes/syncing-server)
  had a documented case
  ([issue #102](https://github.com/standardnotes/syncing-server/issues/102))
  where stable web app + `dev`/`latest` syncing-server produced
  `Syncing: 0/1` plus duplicate cascades. That repo is no longer the
  current self-host backend (the current image is
  `standardnotes/server`), but the lesson — *don't mix
  unstable image tags with stable clients* — still applies.
- **Self-hosted session loop:** Forum
  [issue #3635](https://github.com/standardnotes/forum/issues/3635)
  describes the `No cookies provided for cookie-based session token`
  symptom, traced back to `COOKIE_DOMAIN` / HTTPS / reverse-proxy
  cookie handling and an unstable image tag. Pinning a known-good
  tag was a working mitigation.

<br>

## 1. What is this?

This repository ships **Unraid Community Application templates** for the
[official `standardnotes/server` Docker image](https://hub.docker.com/r/standardnotes/server),
plus a **LocalStack** companion template (required companion for the
official Standard Notes server image — see [§ 2](#2-architecture)) that
mirrors the
[upstream `docker-compose.example.yml`](https://github.com/standardnotes/server/blob/main/docker-compose.example.yml).

What it deliberately does **not** do:

- **No bundled MariaDB.** You bring your own MariaDB container —
  reuse the one you already run for Nextcloud, Vaultwarden, Photoprism,
  whatever. One DB engine for all your apps.
- **No bundled Redis.** Same logic. Reuse your existing Redis container.
- **No bundled web client.** Standard Notes recommends the official
  desktop / mobile apps. If you want a browser client too, the
  optional [`standardnotes/web`](https://standardnotes.com/help/self-hosting/web-app)
  image is shipped as a **separate** Unraid template in the companion
  repo
  [`junkerderprovinz/standardnotes-webui`](../standardnotes-webui/)
  (container name `StandardNotes-WebUI`). Install it on its own and point it
  at this server via your reverse proxy.

What it does do:

- **One Unraid template per concern** — `StandardNotes-Server` and
  the required companion `StandardNotes-LocalStack` (SNS / SQS). The
  browser client lives in the companion repo as its own
  `StandardNotes-WebUI` template.
- **Two templates from one CA submission.** Once this repo is listed
  on the Unraid Community Applications feed, both
  `StandardNotes-Server` and `StandardNotes-LocalStack` appear as
  **separate installable apps** in the Unraid **Apps** tab even
  though they ship from the same GitHub repo and `ca_profile.xml`
  maintainer. Install them one at a time, in the install order
  documented in [§ 2](#install-order-mandatory). The browser client
  (`StandardNotes-WebUI`) appears as a third, separate app from the
  companion [`standardnotes-webui`](../standardnotes-webui/)
  repo. *(CA's exact list grouping in the UI may vary; what matters is
  that each of the three templates is installed as its own container,
  not bundled.)*
- **Sane defaults** taken from the upstream
  [`.env.sample`](https://github.com/standardnotes/server/blob/main/.env.sample).
- **Every secret marked `Mask="true"`** in the template, so the Unraid UI
  hides them by default.
- **Volumes match upstream paths** — `/var/lib/server/logs` and
  `/opt/server/packages/files/dist/uploads`.
- **All in German/English-friendly self-hosting docs**, focused on getting
  you to a working install without surprises.

| | **This template** | Bundled-stack templates |
|---|:---:|:---:|
| Standard Notes server image | ✅ official `standardnotes/server` | ✅ |
| MariaDB / Redis bundled | ❌ (reuse your existing MariaDB / Redis) | ✅ |
| LocalStack as a separate, required companion | ✅ | ⚠️ embedded |
| Secrets masked in UI | ✅ | ⚠️ |
| Reverse-proxy guidance | ✅ | ⚠️ |
| Volumes match upstream paths 1:1 | ✅ | ⚠️ |

### Scope: backend only, no paid-feature unlocks, no AiO image

This template ships **only the official Standard Notes backend**
(`standardnotes/server`) plus the required LocalStack companion. A few
points users frequently ask about:

- **Paid Standard Notes features are not unlocked by self-hosting.**
  Subscription-only client features (extended editors, advanced themes,
  Files quota, Listed, etc.) are gated by Standard Notes' own licensing
  / subscription checks, which live in the official clients and the
  upstream server. This template **does not** patch, bypass, or
  otherwise modify those checks — it deploys the upstream image as-is.
  Self-hosting gives you data ownership and a free Sync server; it does
  not turn a free account into a paid one.
- **Web UI is intentionally a separate, optional container.** If you
  want a browser client in addition to the desktop / mobile apps, run
  the official [`standardnotes/web`](https://standardnotes.com/help/self-hosting/web-app)
  image as its **own** Unraid container and point it at this server via
  your reverse proxy. The companion template
  [`junkerderprovinz/standardnotes-webui`](../standardnotes-webui/)
  ships exactly that — container name `StandardNotes-WebUI`, default host
  port `3001` to avoid the backend's `:3000`. Keeping web and server
  separate mirrors upstream's own `docker-compose.example.yml`, makes
  upgrades independent, and avoids the maintenance burden of a custom
  rebuilt all-in-one image.
- **No All-in-One (AiO) container.** An AiO image bundling server +
  web + DB + cache is **not** planned for the first Community
  Applications release. AiO would require a custom rebuilt image
  (diverging from upstream tags), would re-bundle MariaDB / Redis that
  most Unraid users already run, and would have to be re-released on
  every upstream component bump. This wrapper deliberately stays close
  to upstream so updates are just a tag change.

<br>

## 2. Architecture

```
┌──────────────────────────── Unraid Host ────────────────────────────┐
│                                                                     │
│   Reverse Proxy                                                     │
│   (SWAG / NPM / Traefik)  ──HTTPS──►  StandardNotes-Server           │
│                                       (standardnotes/server)        │
│                                       :3000  API gateway            │
│                                       :3104  files server           │
│                                            │                        │
│                              ┌─────────────┼──────────────┐         │
│                              ▼             ▼              ▼         │
│                          MariaDB       Redis        StandardNotes-  │
│                         (separate)   (separate)      LocalStack     │
│                                                       (sns, sqs)    │
└─────────────────────────────────────────────────────────────────────┘
```

The Standard Notes server image talks to:

- **MariaDB** — schema migrations run automatically on first start.
- **Redis** — cache, queues, rate limits.
- **LocalStack** — **required companion** for the official
  `standardnotes/server` image. Provides the SNS / SQS endpoints the
  worker process expects to reach at `localstack:4566` on every
  self-hosted setup. Without it, `files-worker.log` fills with
  `SQSError: SQS receive message failed: getaddrinfo ENOTFOUND
  localstack` and background jobs stall — destabilising sync and
  contributing to duplication. Earlier passes called LocalStack
  *optional*; live installs show it is required for a stable full
  install.

### Why each component is required

| Component | Role | What breaks if missing |
|---|---|---|
| **MariaDB** | Persistent store for users, items (encrypted note blobs), sessions, settings and migration metadata. | Server fails to start — no schema, no auth, no notes. |
| **Redis** | Cache, ephemeral session state, rate-limit counters, sync deduplication state shared across worker processes. | Sessions and `/v1/items` sync state are not deduplicated correctly across requests; `ECONNREFUSED` / timeout in logs; sync loops and duplicate notes become possible. |
| **StandardNotes-LocalStack** | Emulates AWS SNS topics and SQS queues that `standardnotes/server` workers (auth, syncing-server, files, revisions, analytics, scheduler) publish to and consume from. Bootstrap script pre-creates the exact topics / queues upstream expects. | `files-worker.log` fills with `getaddrinfo ENOTFOUND localstack`; even when TCP-reachable but **unbootstrapped**, account creation hangs and the first note duplicates infinitely. |
| **StandardNotes-Server** | Standard Notes API gateway, sync server, auth server and files server, all in one image. End-to-end-encrypted note bodies are stored encrypted; the server cannot read them. | The whole stack — no API to talk to. |
| **StandardNotes-WebUI** *(separate repo)* | Official `standardnotes/web` browser client. Pure static UI served on container port `80`; the sync server is configured per-browser at runtime via *Advanced options → Custom Sync Server*. | Optional — desktop / mobile apps work without it. Without it you simply have no browser client. |

### Install order (mandatory)

The components must be brought up in this order. Each step expects the
previous step to already be reachable from the Unraid host *and* from
inside the next container.

1. **MariaDB** (external, your existing container). Create
   `standard_notes_db` and a `std_notes_user` with `ALL PRIVILEGES`
   on it before continuing. See [§ 5](#5-database--cache).
2. **Redis** (external, your existing container). Default port `6379`,
   no auth, on a network the server container can route to. See
   [§ 5](#5-database--cache).
3. **StandardNotes-LocalStack** (this repo, companion). Drop the
   bootstrap script on the Unraid host **before** first start so the
   init hook runs automatically (see [§ 3 Step 2](#step-2--start-localstack-required-companion)).
4. **StandardNotes-Server** (this repo, main template). On
   `br0` / macvlan / VLAN / static-IP installs, append
   `--add-host=localstack:<LocalStack-IP>` to *Extra Parameters*
   **before** starting it for the first time — Docker's embedded DNS
   does not resolve container names across `br0` / macvlan, and
   without `--add-host` the workers cannot find `localstack`.
5. **StandardNotes-WebUI** *(optional)* from the separate companion
   repo [`standardnotes-webui`](../standardnotes-webui/).
   Install last — it only needs the backend's public HTTPS URL.
6. **Reverse-proxy hosts (NPM / SWAG / Traefik / Caddy)** for the
   backend, optional files server, and WebUI. These can be created any
   time after the corresponding container is running, but **must exist
   before** a real client (desktop, mobile, browser) is pointed at the
   server — clients require HTTPS, and `Secure` session cookies are
   dropped over plain HTTP. See [§ 8](#8-reverse-proxy).

<br>

## 3. Quick Start on Unraid

> ✅ **Validated end-to-end on Unraid** with a static-IP / VLAN setup
> after (1) Redis was made reachable from the server container, (2)
> LocalStack was bootstrapped with the upstream SNS/SQS init script,
> and (3) the `localstack` hostname was mapped on the server container
> via `--add-host=localstack:<LocalStack-IP>`. Applying those three
> steps resolved the duplicate-note loop observed during testing; the
> stack has since run cleanly through account creation, single- and
> multi-client sync, and the troubleshooting probes documented in
> [§ 0](#0-sync-loop--duplicate-notes-guardrails) and
> [§ 11](#11-troubleshooting).

### Step 0 — Pre-flight

You will need:

- An Unraid server with **Community Applications** installed.
- A **MariaDB** container reachable from the Unraid host — see
  [§ 5](#5-database--cache).
- A **Redis** container reachable from the Unraid host — see [§ 5](#5-database--cache).
- A **LocalStack** container resolvable as the hostname `localstack`
  from the server container — required companion, see
  [§ 2](#2-architecture).
- Three 32-byte hex secrets — see [§ 4](#4-generating-secrets).
- A reverse proxy with HTTPS — see [§ 8](#8-reverse-proxy).

### Step 1 — Install the templates

The repository ships two templates:

- `templates/standardnotes-server.xml` — the Standard Notes backend.
- `templates/standardnotes-localstack.xml` — required companion SNS /
  SQS provider (must be reachable at `localstack:4566` from the
  server container — see [§ 2](#2-architecture)).

Pull the templates into Unraid's user-template folder via the Unraid
console / SSH:

```bash
mkdir -p /boot/config/plugins/dockerMan/templates-user

curl -fsSL -o /boot/config/plugins/dockerMan/templates-user/my-StandardNotes-Server.xml \
  https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/standardnotes-server.xml

curl -fsSL -o /boot/config/plugins/dockerMan/templates-user/my-StandardNotes-LocalStack.xml \
  https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/standardnotes-localstack.xml
```

> 📌 The Unraid templates-user destination is
> `/boot/config/plugins/dockerMan/templates-user/`. Templates dropped
> there appear under **Docker → Add Container → Template → User
> templates** without restarting Docker.

### Step 2 — Start LocalStack (required companion)

**First**, drop the bootstrap script on the Unraid host. LocalStack
starts empty and `standardnotes/server` workers expect a fixed set
of SNS topics and SQS queues — without them, account creation hangs
and notes can duplicate even though TCP `4566` connects fine.
Upstream solves this by mounting a one-time init script into
`/etc/localstack/init/ready.d/`; this repo ships the same script at
[`scripts/localstack_bootstrap.sh`](scripts/localstack_bootstrap.sh).

On the Unraid host, **before** starting the LocalStack container:

```bash
mkdir -p /mnt/user/appdata/standardnotes
curl -fsSL -o /mnt/user/appdata/standardnotes/localstack_bootstrap.sh \
  https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/scripts/localstack_bootstrap.sh
chmod +x /mnt/user/appdata/standardnotes/localstack_bootstrap.sh
```

Then, in the Unraid Web UI: **Docker** → **Add Container** → in the
**Template** dropdown, pick **StandardNotes-LocalStack** under
*User templates*. Leave the *LocalStack Bootstrap Script* Path
mapping at its default — it points at the file you just placed.

- **User-defined Docker network setup** (server + LocalStack on the
  same custom bridge): no further configuration needed — give the
  LocalStack container the network alias `localstack` (Unraid:
  Advanced → Network alias) and Docker's embedded DNS will handle
  the rest.
- **`br0` / macvlan / VLAN / static-IP setup** (e.g. each container
  pinned to its own fixed IP on `br0.<vlan>`): set the LocalStack
  container's *Network Type* to the same `br0`-VLAN as
  `StandardNotes-Server` and give it a **fixed IP** (e.g.
  `192.168.x.x`). Then, in `StandardNotes-Server`'s **Extra
  Parameters**, **append** `--add-host=localstack:<LocalStack-IP>`
  (substituting the IP you assigned). Docker's embedded DNS does
  *not* resolve container names across `br0` / macvlan — `--add-host`
  is what makes the literal name `localstack` resolve in this case.

Hit **Apply**. Once LocalStack reports ready, verify the bootstrap
script created the topics and queues:

```bash
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sqs list-queues
docker exec StandardNotes-LocalStack \
  awslocal --endpoint-url=http://localhost:4566 sns list-topics
```

Expected: each command lists multiple `*-local-queue` /
`*-local-topic` entries (`auth-local-queue`,
`syncing-server-local-queue`, `files-local-queue`,
`revisions-server-local-queue`, `analytics-local-queue`,
`scheduler-local-queue`, plus the matching topics). An empty
`Queues: []` / `Topics: []` means the script never ran — most often
because the host file was missing on first start. Fix the host
file and either recreate the container, or use the **emergency
bootstrap** under
[§ 0](#emergency-bootstrap-localstack-already-running-no-queues) to
populate the running container in place.

> ⚠️ **LocalStack is required for a stable full install** of the
> official `standardnotes/server` image. The worker process resolves
> the hostname `localstack` for SNS / SQS; if that name does not
> resolve, `files-worker.log` repeats `getaddrinfo ENOTFOUND
> localstack` and background jobs fail in a loop. After starting
> LocalStack, confirm the server container can resolve and reach it:
>
> ```bash
> docker exec StandardNotes-Server getent hosts localstack
> docker exec StandardNotes-Server node -e "const net=require('net'); \
>   const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
>   s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
>   s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
>   s.on('error',e=>{console.error(e.message); process.exit(1)});"
> ```
>
> Both must succeed before connecting any client. On `br0` / macvlan
> / VLAN / static-IP installs, `getent hosts localstack` returning
> empty (and `getaddrinfo ENOTFOUND localstack` from the node probe)
> means the `--add-host=localstack:<LocalStack-IP>` mapping is
> missing from `StandardNotes-Server`'s *Extra Parameters* — add it
> and restart the server container. See
> [§ 11](#11-troubleshooting) and
> [`docs/sync-loop-troubleshooting.md`](docs/sync-loop-troubleshooting.md)
> for more.

### Step 3 — Start the Standard Notes server

**Docker** → **Add Container** → pick **StandardNotes-Server** under
*User templates*. Fill in:

- **DB Host / Port / Username / Password / Name** → values of your MariaDB
  container.
- **Redis Host / Port** → values of your Redis container.
- **JWT Secret / Auth Server Encryption Key / Valet Token Secret** → three
  outputs of `openssl rand -hex 32` (see [§ 4](#4-generating-secrets)).

Hit **Apply**. First start runs the schema migrations, which can take
20–60 seconds. Watch the container log; you should eventually see the
API gateway listening on port 3000.

#### Example values (shape reference)

Substitute your own hosts, domain, and DB password (never paste a real
password into a public template).

| Field | Example value |
|---|---|
| Public sync URL | `https://standardnotesserver.mydomain.tld` |
| Server container static IP | `192.168.x.x` |
| MariaDB Host | `192.168.x.x` |
| MariaDB Port | `3306` |
| MariaDB User | `std_notes_user` |
| MariaDB Password | *(your own — store in password manager)* |
| MariaDB Database Name | `standard_notes_db` *(already created)* |
| Database Driver (`DB_TYPE`) | `mysql` *(internal driver value required for MariaDB — see § 6)* |
| Redis Host | `192.168.x.x` |
| Redis Port | `6379` |
| Cookie Domain (`COOKIE_DOMAIN`) | `standardnotesserver.mydomain.tld` *(bare domain — no `https://`)* |
| Public Files Server URL (`PUBLIC_FILES_SERVER_URL`) | *(optional)* `https://files.standardnotesserver.mydomain.tld` *(full HTTPS URL — includes `https://`)* — leave empty to skip attachments — see [§ 8](#8-reverse-proxy) |
| Custom Sync Server *(entered in the client / web app)* | `https://standardnotesserver.mydomain.tld` *(full HTTPS URL)* |

> 💡 This template asks for **IP addresses** for the MariaDB and Redis
> hosts. IPs are unambiguous across Unraid's bridge / `br0` / VLAN
> setups and do not silently break when Docker bridge names get
> reassigned. Use a static / DHCP-reserved address so the IP doesn't
> change on container restart.

### Step 4 — Reverse-proxy & connect a client

Point your reverse proxy at `http://<unraid-ip>:3000`. Open the official
[Standard Notes app](https://standardnotes.com/download) → **Advanced
options** on the sign-up screen → enter `https://your-domain/` as the
**Sync Server**. Create your account.

<br>

## 4. Generating Secrets

The server image requires three high-entropy secrets. Generate each with
**openssl** on any Linux/Mac host (or under WSL, or inside the Unraid
console):

```bash
openssl rand -hex 32   # AUTH_JWT_SECRET
openssl rand -hex 32   # AUTH_SERVER_ENCRYPTION_SERVER_KEY
openssl rand -hex 32   # VALET_TOKEN_SECRET
```

Each command prints a 64-character hex string. Paste them into the
matching fields in the Unraid template.

> ⚠️ **Treat these as write-once.** Rotating `AUTH_SERVER_ENCRYPTION_SERVER_KEY`
> renders existing server-side data unreadable. Back them up to your
> password manager **before** you deploy.

<br>

## 5. Database & Cache

This template intentionally does **not** bundle a database or Redis. Run
them as separate Unraid containers — that way one DB engine and one
Redis serve all your self-hosted apps.

### MariaDB

Use any current MariaDB container. Recommended:

- **MariaDB-Official** (Community Applications).

Create the database and user before starting the Standard Notes container:

```sql
CREATE DATABASE IF NOT EXISTS standard_notes_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'std_notes_user'@'%' IDENTIFIED BY 'use-a-strong-password-here';
GRANT ALL PRIVILEGES ON standard_notes_db.* TO 'std_notes_user'@'%';
FLUSH PRIVILEGES;
```

Then put the resulting `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`,
`DB_DATABASE` values into the Unraid template fields.

> ℹ️ **About `DB_TYPE=mysql`.** Standard Notes' upstream image uses the
> TypeORM `mysql` driver string, which is the same driver used to talk
> to MariaDB. Leave `DB_TYPE=mysql` — it is an **internal driver value
> required for MariaDB**, not an instruction to install MySQL.

### Redis

Any 6.x or 7.x Redis container works. Recommended:

- **Redis-Official** (Community Applications), default port 6379, no auth.

Set the Redis Host field to the **IP address** of your Redis container
(e.g. `192.168.x.x`) and `REDIS_PORT` to `6379`.

> 🔒 **Redis security.** This community template intentionally does
> **not** expose a Redis password field. The official
> `standardnotes/server` image does not document a Redis-auth env var,
> and adding one without verifying upstream support tends to break
> installs. Instead, keep Redis on a **trusted VLAN or private bridge**
> and firewall it off from the public internet. If your particular
> image fork supports Redis auth, verify the env-var name against its
> docs first, then add it as a custom Variable in the template.

<br>

## 6. Configuration Reference

### Server template — environment variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | *(required)* | IP address of your MariaDB container, e.g. `192.168.x.x` |
| `DB_PORT` | `3306` | DB port |
| `DB_USERNAME` | `std_notes_user` | DB user |
| `DB_PASSWORD` | *(required)* | DB password |
| `DB_DATABASE` | `standard_notes_db` | DB name |
| `DB_TYPE` | `mysql` | **Internal driver value required for MariaDB.** Standard Notes / TypeORM uses the `mysql` driver string to talk to MariaDB — leave at `mysql`. |
| `REDIS_HOST` | *(required)* | IP address of your Redis container, e.g. `192.168.x.x` |
| `REDIS_PORT` | `6379` | Redis port |
| `CACHE_TYPE` | `redis` | Leave at `redis` |
| `AUTH_JWT_SECRET` | *(required)* | 32-byte hex — see [§ 4](#4-generating-secrets) |
| `AUTH_SERVER_ENCRYPTION_SERVER_KEY` | *(required)* | 32-byte hex — see [§ 4](#4-generating-secrets) |
| `VALET_TOKEN_SECRET` | *(required)* | 32-byte hex — see [§ 4](#4-generating-secrets) |
| `PUBLIC_FILES_SERVER_URL` | *(empty)* | **Full HTTPS URL** of the files server (includes `https://`), e.g. `https://files.standardnotesserver.mydomain.tld`. Set only when you reverse-proxy the files server on its own subdomain. |
| `COOKIE_DOMAIN` | *(empty)* | **Bare domain only — no protocol, no `https://`, no path.** Example: `standardnotesserver.mydomain.tld` ✅. Wrong: `https://standardnotesserver.mydomain.tld` ❌ (that's a URL — it breaks session cookies). The Custom Sync Server URL entered in clients is a separate value and *is* a full HTTPS URL: `https://standardnotesserver.mydomain.tld`. HTTPS is required for `Secure` cookies outside `localhost`. Wrong value → `No cookies provided for cookie-based session token` and a possible sync loop. See [§ 0](#0-sync-loop--duplicate-notes-guardrails). |

### Ports & Volumes

| Host Port | Container Port | Purpose |
|---|---|---|
| `3000` | `3000` | API gateway (HTTP, behind reverse proxy) |
| `3125` | `3104` | Files server. **Forward your reverse proxy to host port `3125`**, not `3104`. The internal upstream files service listens on `3104` *inside* the container; `3125` is the published host port (per upstream `docker-compose.example.yml`). The Unraid template's *Files Server Port* field reflects this: container target `3104`, default host port `3125`. |

| Volume | Purpose |
|---|---|
| `/var/lib/server/logs` | Server logs |
| `/opt/server/packages/files/dist/uploads` | Encrypted file uploads |

A full upstream-aligned [`examples/.env.example`](examples/.env.example) is
included for reference / non-Unraid use.

<br>

## 7. Security

- **Always** put Standard Notes behind HTTPS — never publish port 3000
  directly. Standard Notes itself is end-to-end encrypted, but TLS still
  matters for auth tokens and metadata.
- **Back up your secrets** (the three `openssl rand -hex 32` outputs)
  alongside your DB backups. Without `AUTH_SERVER_ENCRYPTION_SERVER_KEY`
  the on-disk data is unreadable.
- **Restrict DB / Redis to the bridge network.** Don't publish their
  ports to the host unless you genuinely need external access.
- **Disable user registration** once your accounts exist, if you don't
  want the world signing up. See the
  [official self-hosting docs](https://standardnotes.com/help/self-hosting/getting-started)
  for the relevant environment variable.
- **Patch regularly** — `docker pull standardnotes/server:latest` and
  recreate, see [§ 10](#10-updating).

<br>

## 8. Reverse Proxy

The Standard Notes API gateway is plain HTTP on port 3000. Terminate
TLS in your reverse proxy.

### Nginx Proxy Manager (NPM)

A common Unraid setup is **Nginx Proxy Manager** running on the same
LAN as the Standard Notes container. Example shape (substitute your
own LAN IPs and domain):

| | Value |
|---|---|
| NPM host | `192.168.x.x` |
| Standard Notes server static IP | `192.168.x.x` |
| Public domain | `standardnotesserver.mydomain.tld` |

In the NPM UI, **Hosts → Proxy Hosts → Add Proxy Host**:

- **Domain Names:** `standardnotesserver.mydomain.tld`
- **Scheme:** `http`
- **Forward Hostname / IP:** `192.168.x.x` *(StandardNotes-Server container IP)*
- **Forward Port:** `3000`
- **Block Common Exploits:** on
- **Websockets Support:** on
- **SSL** tab — request a Let's Encrypt cert, **Force SSL** on,
  **HTTP/2 Support** on, **HSTS** on once you've confirmed the cert
  renews automatically.

Then in the Standard Notes template, set:

- `COOKIE_DOMAIN=standardnotesserver.mydomain.tld`
  — **bare domain only**, no `https://`, no trailing slash.
- (optional) `PUBLIC_FILES_SERVER_URL=https://files.standardnotesserver.mydomain.tld`
  — **full HTTPS URL** (with `https://`); set only if you also create a
  separate proxy host for the files server (see below).

In the Standard Notes desktop / mobile / web client, the **Custom Sync
Server** field is also a full HTTPS URL: `https://standardnotesserver.mydomain.tld`.

### Files server — is a second subdomain required?

**Short answer:** No, a second subdomain is not strictly required, but
for any **fully configured public** setup with attachments it is the
recommended path.

The Standard Notes **files server** listens on container port `3104`
internally; the upstream `docker-compose.example.yml` publishes that as
host port `3125` (mapping `3125:3104`). Forward your reverse proxy to
**host port 3125** — never to `3104` directly, since `3104` is the
internal container port and is not exposed by this template. The
official Docker docs expose the sync server on `:3000` and the files
server on `:3125` and configure `PUBLIC_FILES_SERVER_URL` to a separate
URL — that is the upstream shape. Two options:

1. **Skip attachments (simplest).** Leave **Public Files Server URL**
   empty. Note creation, editing, and sync all work — only attachment
   upload/download is disabled. This is the intended path for a
   minimal community-template install.
2. **Two NPM proxy hosts / two subdomains (recommended for full
   attachment support).** Add a second NPM proxy host, e.g.
   `files.standardnotesserver.mydomain.tld` → `192.168.x.x:3125` (the
   StandardNotes-Server container IP), with its own Let's Encrypt
   certificate and **Force SSL** on. Then set
   **Public Files Server URL** = `https://files.standardnotesserver.mydomain.tld`
   in the template.

> ⚠️ **Same-domain / path-prefix proxying is not recommended for this
> community template.** The upstream image documents the two-port,
> two-URL split (sync on `:3000`, files on `:3125` with
> `PUBLIC_FILES_SERVER_URL`). Some operators get a single-domain
> `/files/*` setup working with custom NPM *Advanced* nginx config,
> but it can break across upstream image updates and is not part of
> the supported template default. For stable attachment support,
> give the files server its own subdomain.

### Generic reverse-proxy snippet (SWAG / nginx)

If you are not using NPM, a minimal SWAG (`nginx`) location block:

```nginx
server {
    listen 443 ssl http2;
    server_name standardnotesserver.mydomain.tld;

    include /config/nginx/ssl.conf;

    location / {
        include /config/nginx/proxy.conf;
        resolver 127.0.0.11 valid=30s;
        set $upstream_app 192.168.x.x;
        set $upstream_port 3000;
        set $upstream_proto http;
        proxy_pass $upstream_proto://$upstream_app:$upstream_port;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

If you reverse-proxy the **files server** under a separate hostname
(e.g. `files.standardnotesserver.mydomain.tld`), set
`PUBLIC_FILES_SERVER_URL=https://files.standardnotesserver.mydomain.tld` in
the template's *Public Files Server URL* field.

<br>

## 9. Backup & Restore

Three things to back up, in order of importance:

1. **The three secrets** (`AUTH_JWT_SECRET`,
   `AUTH_SERVER_ENCRYPTION_SERVER_KEY`, `VALET_TOKEN_SECRET`) — store in
   your password manager.
2. **The database** — daily `mysqldump` of `standard_notes_db`, kept
   off-site. The Unraid plugins
   *MariaDB-Backup* / *appdata.backup* both work.
3. **The uploads folder** — `/mnt/user/appdata/standardnotes/uploads`
   (encrypted blobs from the files server).

Restoring is the reverse: provision a fresh DB and Redis, paste the
saved secrets into the template, restore the SQL dump and the uploads
folder, start the container.

<br>

## 10. Updating

```bash
docker pull standardnotes/server:latest
docker stop StandardNotes-Server && docker rm StandardNotes-Server
# re-create with the same template / docker run args
```

On Unraid: **Docker** tab → click the container → **Force Update**. Your
appdata is untouched. Migrations, if any, run automatically on the next
start — watch the log for errors.

<br>

## 11. Troubleshooting

<details>
<summary><b>Container restarts in a loop on first start</b></summary>

- 99% of the time this is a missing or wrong DB credential. Check the
  container log: `connection refused` → wrong host/port; `Access denied
  for user` → wrong username/password.
- Make sure the database `standard_notes_db` exists and the user has
  `ALL PRIVILEGES` on it.
- The MariaDB / Redis container must be **on the same bridge network**.
  Custom `br0`s with isolated IPs need explicit DNS / IP wiring.
</details>

<details>
<summary><b>"Invalid token" / sessions break after a restart</b></summary>

- You changed `AUTH_JWT_SECRET`. Restore the old value, or accept that
  every client has to sign in again.
</details>

<details>
<summary><b>"Cannot decrypt server-side data"</b></summary>

- You changed `AUTH_SERVER_ENCRYPTION_SERVER_KEY`. Restore the old value
  from backup. Without it, the affected on-disk data is permanently
  unreadable.
</details>

<details>
<summary><b>Files server uploads fail</b></summary>

- Confirm port `3125` is reachable through the reverse proxy.
- If the files server is on a separate hostname, set
  `PUBLIC_FILES_SERVER_URL` in the template.
- Check `VALET_TOKEN_SECRET` is set (no default — required).
</details>

<details>
<summary><b>SNS / SQS errors in the log (<code>getaddrinfo ENOTFOUND localstack</code>)</b></summary>

- `getaddrinfo ENOTFOUND localstack` in
  `/var/lib/server/logs/files-worker.log` means the worker cannot
  resolve the hostname `localstack`. LocalStack is the **required
  companion** for the official `standardnotes/server` image — install
  / start it, and ensure DNS resolves before testing notes. Worker
  logs must not show `ENOTFOUND localstack` on a stable install.
- Resolution test from the server container:

    ```bash
    docker exec StandardNotes-Server getent hosts localstack
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

  The first line must print a non-empty result; the second must
  print `LocalStack TCP connected`.
- If `getent` returns empty: containers are not on a shared
  user-defined Docker network. Either put StandardNotes-Server and
  StandardNotes-LocalStack on the **same user-defined Docker
  network** and give LocalStack the network alias `localstack`, or
  — on `br0` / macvlan / VLAN / static-IP installs — install
  `StandardNotes-LocalStack` on the same VLAN with a fixed IP and
  add `--add-host=localstack:<LocalStack-IP>` to the server
  template's *Extra Parameters* (then restart the server container).
- If you have a deliberate alternative SNS / SQS provider, configure
  the matching upstream env vars instead — but for a default
  community-template install, LocalStack is the supported path.

> A files-only deployment (no notes sync — just attachments) can in
> theory skip the queue path, but the upstream image still resolves
> the LocalStack hostname on startup. Even there, worker logs **must
> not** show `ENOTFOUND localstack`.
</details>

<details>
<summary><b>Notes are being duplicated dozens of times in seconds</b></summary>

- **Stop all clients immediately**, stop the server container, do not
  keep editing. See [§ 0](#0-sync-loop--duplicate-notes-guardrails).
- Check the server log for `No cookies provided for cookie-based
  session token`, `ECONNREFUSED`, repeated `/v1/items` 401/500 calls,
  `duplicate_of` cascades, or — in
  `/var/lib/server/logs/files-worker.log` — `SQSError: SQS receive
  message failed: getaddrinfo ENOTFOUND localstack`.
- Verify `REDIS_HOST` / `REDIS_PORT` point at the right **IP** and
  that the Redis container is actually reachable from the
  StandardNotes-Server container (this is the authoritative test —
  same network namespace the server itself uses):

    ```bash
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(6379,'192.168.x.x'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('Redis TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('Redis TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    A throwaway `docker run --rm redis:7-alpine redis-cli -h ... ping`
    is only useful **if** it is launched on a network that can route
    to your Redis container — on `br0` / macvlan / VLAN / static-IP
    setups the default bridge usually cannot. The `redis:7-alpine`
    image is not a second Redis server; it is only a way to get a
    `redis-cli` binary on demand.
- Verify LocalStack is running and the hostname `localstack`
  resolves from the server container (`docker exec StandardNotes-Server
  getent hosts localstack`) — worker logs must not show `ENOTFOUND
  localstack`.
- Verify `COOKIE_DOMAIN` matches your public sync host and that the
  reverse proxy serves the API over **HTTPS**.
- Roll back to a known-good `standardnotes/server` tag if you recently
  upgraded — pin the tag directly in the template's *Repository* field
  (e.g. `standardnotes/server:1.32.0`); see
  [`docs/sync-loop-troubleshooting.md`](docs/sync-loop-troubleshooting.md).
- **Always test with a fresh throwaway account first** before pointing
  your real, long-running client at this server.
</details>

<details>
<summary><b>Unraid edit screen shows template defaults / values look "reset"</b></summary>

- Symptom: opening the StandardNotes-Server (or LocalStack / WebUI)
  container, clicking *Edit*, and seeing all variables back at the
  template defaults — `192.168.x.x`, blank secrets, etc. — even
  right after a successful install.
- Edit the **existing container**, not the template: in Unraid, go
  to *Docker* → click the container's icon → *Edit*. That loads the
  live, saved values for that container. Opening the template from
  *Apps* / *Add Container* / *Templates* re-displays the template
  defaults, which is expected.
- Do **not** overwrite the saved per-container XML
  (`/boot/config/plugins/dockerMan/templates-user/my-StandardNotes-Server.xml`
  and the corresponding `my-StandardNotes-LocalStack.xml` /
  `my-StandardNotes-WebUI.xml`) with `curl` from this repo after you have
  configured the container. The `templates/` files in this repo are
  *new-install* templates; once Unraid has saved a `my-*.xml`, that
  file holds your real values and must not be clobbered.
- This template ships `Config` elements with **inner text equal to
  their `Default=`** attribute (krusader-style) so Unraid's dockerMan
  reliably persists and re-displays each value. If you had an older
  copy of the template without inner text and edited the container
  before this fix, re-installing the container from the updated
  template (or manually re-entering your values once) is enough —
  no data is lost on disk.
</details>

<details>
<summary><b>Client app says "Unable to reach server"</b></summary>

- Try the API directly: `curl https://your-domain/healthcheck`. If that
  fails, the issue is in your reverse proxy, not Standard Notes.
- Mixed-content blocks: clients require HTTPS. Plain `http://` Sync
  Servers are rejected by the desktop / mobile apps.
</details>

<br>

## 12. Contributing / License

Pull requests welcome. Issues:
<https://github.com/junkerderprovinz/unraid-docker-templates/issues>.

> **Support link note / Hinweis zum Support-Link:** The `<Support>` tag in
> both Unraid templates points at the shared support thread for these templates:
> <https://forums.unraid.net/topic/198811-support-junkerderprovinz-unraid-docker-templates/>.
> Der `<Support>`-Link beider Templates zeigt auf diesen gemeinsamen Thread.

**License:** [MIT](LICENSE).

This wrapper repository (Unraid templates, README, banner / icon artwork,
example env file) is MIT-licensed. The upstream `standardnotes/server`,
LocalStack, MariaDB and Redis images retain their own upstream licenses
(Standard Notes: AGPL-3.0; LocalStack: Apache-2.0; MariaDB: GPL-2.0;
Redis: see upstream) — comply with those when running or redistributing
the resulting stack.

```bash
# Validate locally
xmllint --noout templates/*.xml
```

### Credits

- [**Standard Notes**](https://standardnotes.com) — the actual project &
  upstream Docker images
- [**Standard Notes server repo**](https://github.com/standardnotes/server)
  — source of the canonical `.env.sample` and `docker-compose.example.yml`
- [**LocalStack**](https://github.com/localstack/localstack) — SNS / SQS
  emulation
- [**Unraid Community Applications**](https://forums.unraid.net/topic/38582-plug-in-community-applications/)
  — the distribution channel

<br>

## 13. Support this project

If this template saves you a setup hassle or a debug night, consider buying me a coffee:

<p align="center">
  <a href="https://buymeacoffee.com/junkerderprovinz">
    <img src="assets/button-buy-me-a-coffee.svg" alt="Buy me a coffee" width="220">
  </a>
</p>
