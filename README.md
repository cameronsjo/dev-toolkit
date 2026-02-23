# Dev Toolkit

Development workflow tools for building and shipping — logging agents, release pipelines, dependency audits, diagram rendering, and project modernization.

Designed alongside [essentials](https://github.com/cameronsjo/essentials) (desk rhythm) and [rules](https://github.com/cameronsjo/rules) (code standards). Dev-toolkit covers *the tools for building and shipping*.

## Skills

| Skill | Description |
|-------|-------------|
| `logging` | Generate structured log messages with the action-oriented pattern (Preparing → Success → Failure) |
| `dependency-vetting` | Evaluate third-party dependencies for trust and security before adoption |
| `pretty-diagrams` | Create Mermaid diagrams rendered as SVG or ASCII via mmd-render |
| `skill-scout` | Evaluate any GitHub repo — what it does, how to use it, optionally build a skill from it |
| `chunkhound` | Set up ChunkHound semantic code search for large codebases |
| `gibram` | Research and write across large doc corpora with local knowledge graphs |
| `levelup` | Audit and upgrade projects to 2026 tooling (mise, Biome, uv+ruff) |
| `cloud-native-checklist` | Generate CNCF/12-Factor compliance checklists and ADRs |
| `container-signing` | Set up Cosign image signing and SLSA provenance attestations |
| `install-github-app-safely` | Install Claude GitHub App with DDoS/abuse safeguards |
| `sync-description` | Update GitHub repo description from README analysis |

## Commands

| Command | Description |
|---------|-------------|
| `/sync-description` | Update GitHub repo description from README |
| `/install-github-app-safely` | Install Claude GitHub App with safeguards |
| `/modernize-dependencies` | Audit, update, and modernize project dependencies |
| `/setup-release-pipeline` | Set up Beta → RC → Stable release pipeline with GitHub Actions |

## Agents

| Agent | Description |
|-------|-------------|
| `add-logging` | Automatically invoked when adding logging — follows the storytelling philosophy |

## Install

```bash
claude plugin install dev-toolkit@workbench
claude plugin enable dev-toolkit@workbench
```

## License

MIT
