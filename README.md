# Unraid Docker Templates

[![Validate](https://img.shields.io/github/actions/workflow/status/junkerderprovinz/unraid-docker-templates/validate.yml?branch=main&label=Validate&style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/junkerderprovinz/unraid-docker-templates/actions/workflows/validate.yml)
&nbsp;
[![Unraid](https://img.shields.io/badge/Unraid-Templates-f15a2c?style=for-the-badge&logo=unraid&logoColor=white)](https://unraid.net)

Unraid **Community Applications** templates for apps that run from an **upstream Docker image** (no custom build). Containers that ship their **own image** — Krusader, JDownloader, Matrix, featherdrop — live in their own repositories.

## Templates

| App | Description | Folder |
|---|---|---|
| **OpenHands** | Open-source AI software-development agent (local Ollama by default) | [`openhands/`](openhands/) |
| **Standard Notes Server** | Self-hosted Standard Notes sync server (external MariaDB + Redis) | [`standardnotes-server/`](standardnotes-server/) |
| **Standard Notes — LocalStack** | S3-compatible file storage for the Standard Notes server | [`standardnotes-server/`](standardnotes-server/) |
| **Standard Notes Web UI** | Official Standard Notes web client | [`standardnotes-webui/`](standardnotes-webui/) |

## Install

On Unraid: open **Apps** (Community Applications) and search for the app name — these templates are published from this repository.

To add a single template by hand, paste its raw `*.xml` URL into **Add Container → Template**, e.g.
`https://raw.githubusercontent.com/junkerderprovinz/unraid-docker-templates/main/openhands/openhands.xml`

Each app folder has its own README with details and the Unraid support thread.

## License

[MIT](LICENSE)
