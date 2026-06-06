<p align="center">
  <img src=".github/assets/banner.svg" alt="Unraid Docker Templates" width="100%">
</p>

<p align="center">
  <a href="https://github.com/junkerderprovinz/unraid-docker-templates/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/junkerderprovinz/unraid-docker-templates/validate.yml?branch=main&label=Validate&style=for-the-badge&logo=githubactions&logoColor=white" alt="Validate" height="36"></a>&nbsp;
  <a href="#templates"><img src="https://img.shields.io/badge/Templates-5-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Templates" height="36"></a>&nbsp;
  <a href="https://github.com/junkerderprovinz/unraid-docker-templates/commits/main"><img src="https://img.shields.io/github/last-commit/junkerderprovinz/unraid-docker-templates?branch=main&style=for-the-badge&logo=git&logoColor=white&label=Updated" alt="Last commit" height="36"></a>&nbsp;
  <a href="https://unraid.net"><img src="https://img.shields.io/badge/Unraid-Templates-f15a2c?style=for-the-badge&logo=unraid&logoColor=white" alt="Unraid" height="36"></a>&nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License" height="36"></a>
</p>

<p align="center">
Unraid <b>Community Applications</b> templates for apps that run from an <b>upstream Docker image</b> (no custom build). Containers that ship their <b>own image</b> — Krusader, JDownloader, Matrix, featherdrop — live in their own repositories.
</p>

## Templates

| App | Description | Folder |
|---|---|---|
| **OpenHands** | Open-source AI software-development agent (local Ollama by default) | [`openhands/`](openhands/) |
| **Standard Notes Server** | Self-hosted Standard Notes sync server (external MariaDB + Redis) | [`standardnotes-server/`](standardnotes-server/) |
| **Standard Notes LocalStack** | S3-compatible file storage for the Standard Notes server | [`standardnotes-server/`](standardnotes-server/) |
| **Standard Notes Web UI** | Official Standard Notes web client | [`standardnotes-webui/`](standardnotes-webui/) |
| **n8n** | Workflow automation (400+ integrations); PostgreSQL by default, every option exposed | [`n8n/`](n8n/) |

## Install

On Unraid: open **Apps** (Community Applications) and search for the app name — these templates are published from this repository.

To add a single template by hand, paste its raw `*.xml` URL into **Add Container → Template**, e.g.
`https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/openhands/openhands.xml`

Each app folder has its own README with full details. All these templates share one Unraid support thread:
[forums.unraid.net › unraid-docker-templates](https://forums.unraid.net/topic/198811-support-junkerderprovinz-unraid-docker-templates/).

## License

[MIT](LICENSE)
