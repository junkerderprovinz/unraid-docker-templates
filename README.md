<p align="center">
  <img src=".github/assets/banner.svg" alt="Unraid Docker Templates" width="100%">
</p>

<p align="center">
  <a href="https://github.com/junkerderprovinz/unraid-apps/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/junkerderprovinz/unraid-apps/validate.yml?branch=main&label=Validate&style=for-the-badge&logo=githubactions&logoColor=white" alt="Validate" height="36"></a>&nbsp;
  <a href="#templates"><img src="https://img.shields.io/badge/Templates-11-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Templates" height="36"></a>&nbsp;
  <a href="https://github.com/junkerderprovinz/unraid-apps/commits/main"><img src="https://img.shields.io/github/last-commit/junkerderprovinz/unraid-apps?branch=main&style=for-the-badge&logo=git&logoColor=white&label=Updated" alt="Last commit" height="36"></a>&nbsp;
  <a href="https://unraid.net"><img src="https://img.shields.io/badge/Unraid-Templates-f15a2c?style=for-the-badge&logo=unraid&logoColor=white" alt="Unraid" height="36"></a>&nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License" height="36"></a>
</p>

<p align="center">
Unraid <b>Community Applications</b> templates for all of junkerderprovinz's containers — both <b>own-image</b> apps (Krusader, JDownloader, Matrix, featherdrop, BombVault) and <b>upstream-image</b> wrappers (OpenHands, Standard Notes, n8n), plus <b>plugins</b> (ShipLog, SmokeSignal). One repository, one CA feed; each app's image and full source live in its own per-app repository.
</p>


## Containers

*Own images built and published by junkerderprovinz — full docs live in each app's own repository.*

<img src=".github/readme-icons/krusader.png" width="84" align="left" alt="Krusader">
<a href="https://github.com/junkerderprovinz/krusader#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**Krusader**<br>
Twin-pane KDE file manager with a native dark theme, on a fast KasmVNC web desktop (Kate, krename, RAR).

<br clear="all">

<img src=".github/readme-icons/jdownloader.png" width="84" align="left" alt="JDownloader">
<a href="https://github.com/junkerderprovinz/jdownloader#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**JDownloader**<br>
JDownloader 2 with a complete, sleek dark UI out of the box, on a KasmVNC web desktop.

<br clear="all">

<img src=".github/readme-icons/matrix.png" width="84" align="left" alt="Matrix">
<a href="https://github.com/junkerderprovinz/matrix#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**Matrix**<br>
All-in-one Matrix homeserver: Synapse + coturn + Element Web + Synapse-Admin in one container.

<br clear="all">

<img src=".github/readme-icons/featherdrop.png" width="84" align="left" alt="featherdrop">
<a href="https://github.com/junkerderprovinz/featherdrop#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**featherdrop**<br>
Your own private WeTransfer — feather-light, login-free, end-to-end encrypted self-hosted file sharing. Drop a file, set an expiry, share a link.

<br clear="all">

<img src=".github/readme-icons/bombvault.png" width="84" align="left" alt="BombVault">
<a href="https://github.com/junkerderprovinz/bombvault#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**BombVault**<br>
Backup and full disaster recovery for Docker containers, VMs and the flash USB. One-click backup and automatic re-install, powered by restic.

<br clear="all">

## Templates

*Templates for third-party upstream images (no custom build) — full docs in each app's folder below.*

<img src=".github/readme-icons/openhands.png" width="84" align="left" alt="OpenHands">
<a href="openhands/README.md"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**OpenHands**<br>
Open-source AI software-development agent, pre-wired for a local Ollama model.

<br clear="all">

<img src=".github/readme-icons/standardnotes-server.png" width="84" align="left" alt="Standard Notes Server">
<a href="standardnotes-server/README.md"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**Standard Notes Server**<br>
Self-hosted Standard Notes sync server (external MariaDB + Redis). Includes an optional **LocalStack** template for S3-compatible file storage.

<br clear="all">

<img src=".github/readme-icons/standardnotes-webui.png" width="84" align="left" alt="Standard Notes Web UI">
<a href="standardnotes-webui/README.md"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**Standard Notes Web UI**<br>
The official Standard Notes web client.

<br clear="all">

<img src=".github/readme-icons/n8n.png" width="84" align="left" alt="n8n">
<a href="n8n/README.md"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**n8n**<br>
Workflow automation — connect 400+ apps and APIs. PostgreSQL by default, every option exposed in the template form.

<br clear="all">


## Plugins

*Unraid **plugins** (not containers) — listed on CA, installed from the Plugins tab via a `.plg` URL.*

<img src=".github/readme-icons/shiplog.png" width="84" align="left" alt="ShipLog">
<a href="https://github.com/junkerderprovinz/shiplog#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**ShipLog**<br>
Read-only update advisor in Unraid's native Docker tab — a per-container changelog bubble: what changes between your running image and the newest, and how risky, before you press update. Remembers the running version (real "1.7 → 1.8"); optional Ollama summaries + Matrix alerts.

<br clear="all">

<img src=".github/readme-icons/smokesignal.png" width="84" align="left" alt="SmokeSignal">
<a href="https://github.com/junkerderprovinz/smokesignal#readme"><img src="https://img.shields.io/badge/Repository%20%26%20ReadMe-393939?style=for-the-badge&logo=github&logoColor=white" align="right" alt="Repository &amp; ReadMe"></a>

**SmokeSignal**<br>
Pre-reboot health check — a single **GO / CAUTION / NO-GO** verdict before you reboot, so you never reboot into a known landmine. Advisory only.

<br clear="all">


## Install

On Unraid: open **Apps** (Community Applications) and search for the app name — these templates are published from this repository.

To add a single template by hand, paste its raw `*.xml` URL into **Add Container → Template**, e.g.
`https://raw.githubusercontent.com/junkerderprovinz/unraid-apps/main/openhands/openhands.xml`

Containers link to their dedicated repository's README; template (upstream-image) apps keep their README in their folder here.

**Plugins** (ShipLog, SmokeSignal) are published from this repository too — CA lists them the same way as containers (a template with `<Plugin>True</Plugin>` + `<PluginURL>`), so search for them in **Apps**. You can also install a plugin directly from **Plugins → Install Plugin** with its raw `.plg` URL, e.g.
`https://raw.githubusercontent.com/junkerderprovinz/smokesignal/main/plugin/smokesignal.plg`
