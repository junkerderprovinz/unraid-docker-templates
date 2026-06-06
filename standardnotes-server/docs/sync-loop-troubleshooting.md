# Sync-Loop / Duplicate Notes Troubleshooting

> Practical checklist for self-hosted Standard Notes on Unraid when
> notes start duplicating, syncing in a loop, or the client shows
> `Syncing: 0/1` indefinitely. German/English friendly.

This document is the long-form companion to
[§ 0 of the README](../README.md#0-sync-loop--duplicate-notes-guardrails).
Read that section first.

> ⚠️ If duplication is **happening right now**: stop every connected
> client, stop the `StandardNotes-Server` container, and **do not keep
> editing notes**. Every additional edit can fan out further. Diagnose
> first, then resume.

## Emergency checklist (duplicate-loop happening NOW)

Run these in order. Do **not** keep editing notes between steps.

1. **Stop every connected client immediately.** Sign out of web UI,
   desktop, and mobile (don't just close — sign out, so background sync
   stops). Disconnect any browser tab still open against the sync
   server.
2. **Stop the `StandardNotes-Server` container.** Unraid → Docker →
   Stop. Leave MariaDB, Redis and LocalStack running so you can
   inspect state.
3. **Do NOT reconnect any existing client.** Especially not your
   long-history account. Each new edit can fan more duplicates out.
4. **Verify Redis is reachable from `StandardNotes-Server`.**
   The authoritative test runs from **inside** the running server
   container (the network namespace Redis is actually accessed from).
   When the server is up:

    ```bash
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(6379,'192.168.x.x'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('Redis TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('Redis TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    Expected: `Redis TCP connected`. A timeout means a firewall /
    VLAN / `br0` routing problem between the server container and
    the Redis host — fix that first. Also tail the server log for
    `ECONNREFUSED` / connection-timeout lines:
    `docker logs StandardNotes-Server | grep -E "ECONNREFUSED|redis"`.

    If the server container is stopped and you want a quick CLI ping
    via the official `redis-cli`, you can launch it as a **disposable
    client container** (no second Redis server, just `redis-cli` on
    demand):

    ```bash
    docker run --rm --network <same-network-as-redis> \
      redis:7-alpine redis-cli -h 192.168.x.x -p 6379 ping
    ```

    `redis:7-alpine` here is **not** a second Redis server — it is
    only a way to get the `redis-cli` binary. On `br0` / macvlan /
    VLAN / static-IP setups the default `docker run` lands on the
    **default bridge**, which usually cannot route to a VLAN
    container — so `--rm redis:7-alpine redis-cli ping` will time
    out even when Redis is healthy. Always pass `--network` (or
    `--ip` on the same `br0` / macvlan network as Redis), or skip
    this client test entirely and trust the in-container `node -e`
    probe above as the source of truth.
5. **Verify LocalStack is running and resolvable as `localstack`.**
   LocalStack is the **required companion for the official Standard
   Notes server image**. The worker resolves the literal hostname
   `localstack` for SNS / SQS, so DNS *and* TCP both have to work
   from inside `StandardNotes-Server`:

    ```bash
    docker exec StandardNotes-Server getent hosts localstack
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    The first command must print a non-empty line. Tail
    `/var/lib/server/logs/files-worker.log` for `SQSError: SQS
    receive message failed: getaddrinfo ENOTFOUND localstack`. If
    you see it, fix LocalStack reachability *before* reconnecting
    any client.

    **TCP-reachable is not enough — the SNS / SQS resources must
    also exist.** LocalStack starts empty; `standardnotes/server`
    workers expect a fixed set of topics and queues created by
    upstream's `docker/localstack_bootstrap.sh` (this repo ships it
    at `scripts/localstack_bootstrap.sh` and the LocalStack template
    mounts it at `/etc/localstack/init/ready.d/`). If the host file
    was missing at first start, the duplicate-loop symptoms persist
    even with LocalStack TCP connected. Verify:

    ```bash
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sqs list-queues
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sns list-topics
    ```

    Both must list `*-local-queue` / `*-local-topic` entries
    (`auth-local-queue`, `syncing-server-local-queue`,
    `files-local-queue`, `revisions-server-local-queue`,
    `analytics-local-queue`, `scheduler-local-queue` and the matching
    topics). Empty `Queues: []` / `Topics: []` means the bootstrap
    never ran — fix in place with the *Emergency bootstrap* recipe in
    [§ 2a-bis](#2a-bis-localstack-bootstrap-snssqs-queues-missing) below.

    > 📌 **Static IP / `br0` / macvlan / VLAN.** Docker's embedded
    > DNS (`127.0.0.11`) only resolves container names / aliases
    > when both containers share a **user-defined Docker network**.
    > Containers assigned a static IP on `br0` / macvlan / `br0.<vlan>`
    > bypass that DNS and will *not* resolve `localstack`. Working
    > fixes:
    >
    > - Put `StandardNotes-Server` and `StandardNotes-LocalStack`
    >   on the **same user-defined Docker network**, and give the
    >   LocalStack container the **network alias `localstack`**
    >   (Unraid: Advanced → Network alias).
    > - Or, keep `br0` / macvlan / VLAN and **install
    >   `StandardNotes-LocalStack` on the same VLAN with its own
    >   fixed IP** (e.g. `192.168.x.x`), then add the host mapping
    >   to `StandardNotes-Server`'s *Extra Parameters*:
    >   `--add-host=localstack:<LocalStack-IP>`. `getent hosts
    >   localstack` from `StandardNotes-Server` must then return
    >   that IP, and the `node -e` probe to `localstack:4566` must
    >   succeed before any client reconnects.
6. **Check `COOKIE_DOMAIN` is a BARE DOMAIN, and the Custom Sync
   Server URL in the client is a FULL HTTPS URL.** These two values
   are NOT the same shape:
   - `COOKIE_DOMAIN` = `standardnotesserver.mydomain.tld` ✅ (no
     protocol, no slash)
   - Wrong: `COOKIE_DOMAIN=https://standardnotesserver.mydomain.tld` ❌
     (this is a URL — the server emits cookies for the literal string
     `https://...` and no browser will accept them)
   - Custom Sync Server (in client) = `https://standardnotesserver.mydomain.tld` ✅
     (full HTTPS URL, with scheme)
7. **If the test/throwaway account has duplicated:** delete the test
   account, or drop and recreate the database before continuing — do
   not bring the server back up against a corrupted account, or the
   first reconnecting client will reproduce the cascade. Recipe:
   - `mysqldump` → snapshot first (see § 7 below).
   - Drop & recreate `standard_notes_db`, or sign in via the official
     client and delete the corrupted account.
   - Recreate the test account fresh and re-run § 1 *Test plan*.

After the emergency stop, work through the rest of this document
(§§ 2–6) to identify the root cause before bringing the server back
up.

---

## 0. Reference incidents (read once)

| Source | What it says | Status |
|---|---|---|
| [Standard Notes — *How do I clear duplicates?*](https://standardnotes.com/help/33/how-do-i-clear-duplicates) | Duplicates are **app-side conflict resolution**. The server cannot decrypt or merge notes, so the client duplicates conflicting copies to avoid silent data loss. | Current, official |
| [Forum #3635 — self-hosted session loop](https://github.com/standardnotes/forum/issues/3635) | `No cookies provided for cookie-based session token` + `/v1/items` loop traced to `COOKIE_DOMAIN` / HTTPS / reverse-proxy cookie handling and an unstable image tag. Pinning a known-good tag mitigated. | Current |
| [Legacy `standardnotes/syncing-server` #102](https://github.com/standardnotes/syncing-server/issues/102) | Stable web app + `dev`/`latest` syncing-server caused `Syncing: 0/1` and duplicate cascades. Fixed by pinning a stable tag. | **Historical / legacy.** That repo is archived; the current backend image is `standardnotes/server`. The class of failure (unstable tag vs. stable client) is still possible. |

---

## 1. Test plan — *before* you migrate any real notes

Do this on a brand-new account, not on your real one.

- [ ] Create a **fresh throwaway account** on the new self-hosted server.
- [ ] Sign in from **exactly one client** (web or desktop, not both).
- [ ] **Create one note.** Type a few words, save, wait 30 seconds.
- [ ] Refresh / reopen the client. Confirm the note exists **once**.
- [ ] Repeat with a second note, then a third. Watch the server log
      while you do — there should be no `ECONNREFUSED`, no
      `No cookies provided …`, no `duplicate_of` cascade.
- [ ] Only **after** the throwaway account has round-tripped cleanly
      for several notes: connect a second client (mobile/desktop),
      let it sync, and verify the same notes appear once each.
- [ ] **Do not** sign your real, long-history account in until the
      above is stable for at least a full sync cycle.
- [ ] **Make a decrypted export** from your existing Standard Notes
      account (cloud or old self-host) before reconnecting any real
      client. *Account → Data backups → Decrypted backup.*

If any step above misbehaves, stop and work through the rest of this
document before continuing.

---

## 2. Redis reachability

Standard Notes uses Redis for cache, queues, and rate-limiting. If
Redis is unreachable, sync de-duplication and session state get
inconsistent — a known precursor to duplicate cascades.

- [ ] In the Unraid template, **Redis Host** is set to the **IP
      address** of your Redis container (e.g. `192.168.x.x`).
      Use a static / DHCP-reserved address so the IP doesn't change
      on container restart.
- [ ] `REDIS_PORT=6379` (or whatever your Redis container actually
      listens on).
- [ ] **The `StandardNotes-Server` container itself** can reach the
      Redis IP/port — this is the authoritative test on `br0` /
      macvlan / VLAN / static-IP installs, because it runs in the
      same network namespace the server actually talks to Redis from:

    ```bash
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(6379,'192.168.x.x'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('Redis TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('Redis TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    Or, if `nc` is available in the image:

    ```bash
    docker exec -it StandardNotes-Server sh
    # inside the container (replace with your Redis IP):
    nc -zv 192.168.x.x 6379    # should print "open"
    # or, if nc is unavailable:
    timeout 2 sh -c 'cat </dev/tcp/192.168.x.x/6379' && echo OK
    ```

- [ ] *(Optional)* CLI ping via a **disposable `redis-cli` client
      container** — useful only if you already have the network path
      sorted. `redis:7-alpine` is **not a second Redis server**; it's
      just a one-shot way to get the `redis-cli` binary:

    ```bash
    docker run --rm --network <same-network-as-redis> \
      redis:7-alpine redis-cli -h 192.168.x.x -p 6379 ping
    ```

    On `br0` / macvlan / VLAN / static-IP setups the default `docker
    run` lands on the **default bridge**, which usually cannot route
    to a VLAN container — so the bare `docker run --rm redis:7-alpine
    redis-cli ping` form (without `--network`) is not a definitive
    test for those setups and will time out even when Redis is
    healthy. The in-container `node -e` probe above is the
    authoritative test; treat this CLI form as a convenience only.

- [ ] **Expected failure mode if wrong:** the server log emits
      `ECONNREFUSED` (port closed) or connection timeouts (firewall /
      routing) against your Redis host on every sync request. The
      client appears to "save" notes but the server never confirms —
      clients re-send, and conflict logic on the app side can begin
      duplicating.

---

## 2a. LocalStack (SNS / SQS) reachability

LocalStack is the **required companion for the official Standard
Notes server image**. The worker process resolves the literal
hostname `localstack` (default port `4566`) for SNS / SQS. If that
name does not resolve, `/var/lib/server/logs/files-worker.log` fills
with `SQSError: SQS receive message failed: getaddrinfo ENOTFOUND
localstack`, background jobs fail in a loop, and sync gets unstable.

A files-only deployment can in theory skip the queue path, but the
upstream image still resolves `localstack` on startup. Even there,
worker logs **must not** show `ENOTFOUND localstack`.

- [ ] The `StandardNotes-LocalStack` companion container is running.
- [ ] From `StandardNotes-Server`, the hostname `localstack` resolves
      and the edge port responds:

    ```bash
    docker exec StandardNotes-Server getent hosts localstack
    docker exec StandardNotes-Server node -e "const net=require('net'); \
      const s=net.connect(4566,'localstack'); s.setTimeout(5000); \
      s.on('connect',()=>{console.log('LocalStack TCP connected'); s.end(); process.exit(0)}); \
      s.on('timeout',()=>{console.error('LocalStack TCP timeout'); process.exit(1)}); \
      s.on('error',e=>{console.error(e.message); process.exit(1)});"
    ```

    The first command must print a non-empty line. The second must
    print `LocalStack TCP connected`.

- [ ] **If `getent` returns empty:** the two containers are not on a
      shared user-defined Docker network. Docker's embedded DNS
      (`127.0.0.11`) only resolves container names / aliases when
      both containers share a user-defined Docker network. Containers
      on `br0` / macvlan / `br0.<vlan>` with a static IP bypass that
      DNS. Two working fixes:

      - **User-defined Docker network + alias `localstack`** — put
        both containers on the same custom bridge and either name
        the LocalStack container `localstack` or assign it the
        network alias `localstack` (Unraid: Advanced → Network
        alias).
      - **`br0` / macvlan / VLAN / static-IP install** — install /
        start `StandardNotes-LocalStack` on the **same VLAN** as
        `StandardNotes-Server` and assign it a **fixed IP**
        (e.g. `192.168.x.x`). Then, in `StandardNotes-Server`'s
        *Extra Parameters*, **append**
        `--add-host=localstack:<LocalStack-IP>` (substituting the IP
        you assigned). Restart the server container. `getent hosts
        localstack` must then return that IP, and the `node -e`
        probe to `localstack:4566` must succeed before any client
        reconnects.

- [ ] Tail `files-worker.log` and confirm there are **no**
      `getaddrinfo ENOTFOUND localstack` lines after the fix:

    ```bash
    docker exec StandardNotes-Server \
      tail -n 200 /var/lib/server/logs/files-worker.log
    ```

- [ ] **Expected failure mode if wrong:** `SQSError: SQS receive
      message failed: getaddrinfo ENOTFOUND localstack` repeats in
      `files-worker.log`; the worker pipeline stalls; sync gets
      flaky and (with multiple clients online) duplication can
      cascade.

---

## 2a-bis. LocalStack bootstrap (SNS/SQS queues missing)

Distinct failure from § 2a. Here `getent hosts localstack` resolves
and `localstack:4566` accepts TCP — but `sqs list-queues` /
`sns list-topics` come back **empty**. `standardnotes/server`'s
workers then loop on missing-queue errors (no `ENOTFOUND` line in
that case — symptom is account creation hanging and the first note
duplicating infinitely on the client).

LocalStack starts empty. The upstream
[`docker/localstack_bootstrap.sh`](https://raw.githubusercontent.com/standardnotes/server/main/docker/localstack_bootstrap.sh)
script creates the required topics / queues; LocalStack runs anything
under `/etc/localstack/init/ready.d/` once it becomes ready. This
repo ships the same script at `scripts/localstack_bootstrap.sh` and
the Unraid LocalStack template includes a required *LocalStack
Bootstrap Script* Path mapping.

- [ ] Verify the script ran:

    ```bash
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sqs list-queues
    docker exec StandardNotes-LocalStack \
      awslocal --endpoint-url=http://localhost:4566 sns list-topics
    ```

    Both must list `auth-local-queue`, `syncing-server-local-queue`,
    `files-local-queue`, `revisions-server-local-queue`,
    `analytics-local-queue`, `scheduler-local-queue` and the matching
    `*-local-topic` topics.

- [ ] **If empty:** place the script on the host so future restarts
      run the bootstrap:

    ```bash
    mkdir -p /mnt/user/appdata/standardnotes
    curl -fsSL -o /mnt/user/appdata/standardnotes/localstack_bootstrap.sh \
      https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/scripts/localstack_bootstrap.sh
    chmod +x /mnt/user/appdata/standardnotes/localstack_bootstrap.sh
    ```

    Then **either** recreate the LocalStack container (`init/ready.d/`
    only fires once per container lifetime, so a plain restart is not
    always enough on older LocalStack images) **or** bootstrap the
    running container in place:

    ```bash
    curl -fsSL -o /tmp/localstack_bootstrap.sh \
      https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/standardnotes-server/scripts/localstack_bootstrap.sh
    docker cp /tmp/localstack_bootstrap.sh \
      StandardNotes-LocalStack:/tmp/localstack_bootstrap.sh
    docker exec StandardNotes-LocalStack \
      bash /tmp/localstack_bootstrap.sh
    ```

    After the script reports `all topics are:` / `all queues are:`,
    re-run `sqs list-queues` / `sns list-topics` to confirm, then
    **restart `StandardNotes-Server`** so its workers reconnect against
    the now-populated SNS/SQS.

- [ ] **Expected failure mode if wrong:** TCP probe to
      `localstack:4566` succeeds; `getent hosts localstack` returns a
      valid IP; **but** account creation hangs in the client and the
      first note replicates without bound. `files-worker.log` does
      *not* show `ENOTFOUND` — instead it shows repeated SQS errors
      against non-existent queue names. This is the case to suspect
      whenever § 2a passes but duplication persists.

---

## 3. MariaDB reachability and migrations

A half-migrated database is a known cause of strange sync behaviour.

- [ ] `DB_HOST` points at the **IP address** of your MariaDB
      container (e.g. `192.168.x.x`). Use a static / DHCP-reserved
      address.
- [ ] `DB_PORT=3306`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE` all
      match what you created in MariaDB.
- [ ] Database `standard_notes_db` exists with `ALL PRIVILEGES`
      granted to `std_notes_user@'%'`.
- [ ] Watch the **first start** of the server container. The log
      should show schema migrations running for ~20–60 seconds, then
      "API gateway listening on port 3000" (or similar).
- [ ] **Do not log a real client in until migrations have finished
      cleanly.** A login during migrations can end up writing partial
      session state.

---

## 4. Reverse proxy, HTTPS, and `COOKIE_DOMAIN`

This is the area most likely to cause the duplicate-notes / session-loop
class of bug ([forum #3635](https://github.com/standardnotes/forum/issues/3635)).

- [ ] The reverse proxy serves the API over **HTTPS**, not plain HTTP.
      Modern Standard Notes clients reject `http://` sync servers; in
      addition, `Secure` cookies are dropped over HTTP outside
      `localhost`, which produces the
      `No cookies provided for cookie-based session token` symptom.
- [ ] `COOKIE_DOMAIN` is a **bare domain** — no protocol, no
      `https://`, no trailing slash, no path. The Custom Sync Server
      URL entered in the client / web app is a **separate** value and
      *is* a full HTTPS URL. Get this distinction wrong and every
      session breaks:

    | Setting | Value type | Includes `https://`? | Correct example | Wrong example |
    |---|---|---|---|---|
    | `COOKIE_DOMAIN` (env / template) | Bare domain | **No** | `standardnotesserver.mydomain.tld` | `https://standardnotesserver.mydomain.tld` ❌ |
    | `PUBLIC_FILES_SERVER_URL` (env / template) | Full HTTPS URL | **Yes** | `https://files.standardnotesserver.mydomain.tld` | `files.standardnotesserver.mydomain.tld` ❌ |
    | Custom Sync Server (client / web app UI) | Full HTTPS URL | **Yes** | `https://standardnotesserver.mydomain.tld` | `standardnotesserver.mydomain.tld` ❌ |

    Public sync URL → `COOKIE_DOMAIN` mapping:

    | Public sync URL | `COOKIE_DOMAIN` |
    |---|---|
    | `https://notes.example.com` | `notes.example.com` |
    | `https://sn.example.com` | `sn.example.com` |
    | `https://example.com/sn` (path-prefixed) | `example.com` |

- [ ] If you are doing path-prefixed proxying (`example.com/sn`),
      double-check that the proxy preserves the original
      `Host` header and sends `X-Forwarded-Proto: https`.
- [ ] If you change `COOKIE_DOMAIN` later, **all clients have to log
      in again** — old session cookies become invalid.
- [ ] **Expected failure mode if wrong:** server log fills with
      `No cookies provided for cookie-based session token` and the
      client retries `/v1/items` repeatedly (often visible as
      `Syncing: 0/1` in the client status bar).
- [ ] **Files server port — forward to host port `3125`, not
      `3104`.** The internal upstream files service listens on
      `3104` *inside* the container; the published host port is
      `3125` (per upstream `docker-compose.example.yml`,
      `3125:3104`). The Unraid template's *Files Server Port* field
      uses `Target=3104` (container) with `Default=3125` (host). In
      Nginx Proxy Manager / SWAG / Traefik, the *Forward Port* for
      the `files.…` subdomain must be `3125`. Forwarding to `3104`
      will fail (port not exposed on the host).

---

## 5. Image tag — pinning a known-good tag

- [ ] By default the Unraid template uses
      `standardnotes/server:latest`. This is fine for first-time
      installs and matches upstream `docker-compose.example.yml`.
- [ ] If `latest` is **currently regressing** session or sync (forum
      #3635 was an example), pin a known-good release tag in the
      Unraid template's *Repository* field, e.g.
      `standardnotes/server:1.32.0` — replace with whatever
      `standardnotes/server` tag you have last verified. (Unraid's
      `<Repository>` field is the single place to set the tag; it does
      not do env-var interpolation, so there is no separate tag variable.)
- [ ] **Change tags carefully.** Downgrading across schema migrations
      can leave the database in a state the older image cannot read.
      Always: full DB backup → bring server down → swap tag → bring
      server up → watch the log → only then reconnect clients.
- [ ] **Do not mix** a stable client (mobile/desktop store releases,
      stable web app) with a `dev` / `nightly` server tag. That is
      the legacy
      [syncing-server #102](https://github.com/standardnotes/syncing-server/issues/102)
      pattern and although that backend is archived, the same class
      of mismatch can still bite on `standardnotes/server`.

---

## 6. Logs to grep for

When something is wrong, these are the strings that matter. Tail the
container log:

```bash
docker logs -f StandardNotes-Server
```

…and watch for any of the following:

| Log line / pattern | Likely cause |
|---|---|
| `No cookies provided for cookie-based session token` | `COOKIE_DOMAIN` mismatch, missing HTTPS, or proxy stripping cookies. See § 4. |
| `ECONNREFUSED` against your Redis host | Redis container is down, on a different network, or the host/port is wrong. See § 2. |
| Redis connection timeouts (`Operation timed out`) against your Redis host | Firewall / VLAN / `br0` routing problem between the Docker network and the Redis host. See § 2. |
| `SQSError: SQS receive message failed: getaddrinfo ENOTFOUND localstack` (in `/var/lib/server/logs/files-worker.log`) | LocalStack missing, or the hostname `localstack` does not resolve from `StandardNotes-Server`. LocalStack is required, not optional — see § 2a. |
| Repeated SQS errors referencing `*-local-queue` but **no** `ENOTFOUND` line; account creation hangs; first note duplicates infinitely | LocalStack is reachable but **empty** — the `localstack_bootstrap.sh` init script never ran. See § 2a-bis. |
| `ECONNREFUSED` against your DB host | MariaDB is down, on a different network, or credentials/host are wrong. See § 3. |
| `/v1/items` returning 401 in a tight loop | Session not accepted by the server — almost always cookie / `COOKIE_DOMAIN` / HTTPS. See § 4. |
| `/v1/items` returning 500 in a tight loop | Server-side error — check earlier lines for the underlying exception (DB, Redis, migrations). |
| Repeated sync/update cascades, growing `updated_at` storm | Conflict-resolution loop. Stop clients immediately. |
| `duplicate_of` appearing on many notes | Confirmed duplicate cascade — the client is creating conflict copies. Stop clients, see § 7. |

---

## 7. If duplication has already started

Triage order:

1. **Stop all clients.** Sign out of mobile, desktop, and web. Don't
   just close them — sign out so they stop attempting background
   sync.
2. **Stop the server container** in the Unraid Docker tab. Leave
   MariaDB and Redis running so you can inspect state.
3. **Take a database snapshot** *before* any cleanup:

    ```bash
    docker exec -it mariadb sh -c \
      'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" standard_notes_db' \
      > /mnt/user/appdata/standardnotes/dup-incident-$(date +%Y%m%d-%H%M).sql
    ```

4. **Inspect the logs** (see § 6) and identify the root cause —
   Redis, cookies, or image tag are by far the most common.
5. **Fix the root cause first.** Restarting the server without
   fixing the cause will reproduce the loop.
6. **Cleanup of duplicates** is documented by Standard Notes
   themselves: <https://standardnotes.com/help/33/how-do-i-clear-duplicates>.
   Use the official client procedure rather than touching the
   database directly — the server cannot decrypt notes, so
   server-side deduplication is not possible.
7. Only after the root cause is fixed and duplicates are cleaned, log
   one client back in and verify a single new note round-trips
   cleanly **before** reconnecting any other client.

---

## 8. References

- [Standard Notes — *How do I clear duplicates?*](https://standardnotes.com/help/33/how-do-i-clear-duplicates)
  — official duplicate-handling docs.
- [Forum issue #3635 — self-hosted session loop](https://github.com/standardnotes/forum/issues/3635)
  — `COOKIE_DOMAIN` / HTTPS / image-tag root cause.
- [Legacy `standardnotes/syncing-server` issue #102](https://github.com/standardnotes/syncing-server/issues/102)
  — historical stable-client / dev-server mismatch causing
  `Syncing: 0/1` and duplicates. Archived backend; class of failure
  still relevant.
- [Standard Notes self-hosting docs](https://standardnotes.com/help/self-hosting/getting-started)
- [`standardnotes/server` upstream `.env.sample`](https://github.com/standardnotes/server/blob/main/.env.sample)
