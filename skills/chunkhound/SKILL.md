---
name: chunkhound
description: Use when setting up ChunkHound for semantic code search on a large or unfamiliar codebase, enabling the chunkhound MCP server so Claude can answer "how does X work" questions across thousands of files, or when local-first AI-accessible indexing is needed.
---

# ChunkHound

ChunkHound is a local-first semantic code search tool that runs as an MCP server. It indexes your codebase using AST-aware chunking and exposes `search` and `research` tools to Claude via MCP.

## When to Use

- Codebase has 10k+ files and grep/glob aren't cutting it
- Need to answer "how does authentication work end-to-end?" across the full repo
- Code must stay local (security-sensitive, no cloud indexing)
- Onboarding to an unfamiliar monorepo
- Multi-language codebase needing unified semantic search

Skip it for small projects where `Grep` is fast enough.

## Prerequisites

- Python 3.10–3.13 (not 3.14+)
- [uv](https://astral.sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Install

```bash
uv tool install chunkhound
chunkhound --version
```

## Configure

Create `.chunkhound.json` in the project root. Do **not** put API keys here if the repo is shared — use env vars instead (`CHUNKHOUND_EMBEDDING__API_KEY`).

**VoyageAI (recommended — best retrieval quality):**
```json
{
  "embedding": {
    "provider": "voyageai",
    "api_key": "pa-your-key",
    "model": "voyage-3.5",
    "rerank_model": "rerank-lite-1"
  },
  "llm": { "provider": "claude-code-cli" }
}
```

**OpenAI (if you already have a key):**
```json
{
  "embedding": {
    "provider": "openai",
    "api_key": "sk-your-key",
    "model": "text-embedding-3-small"
  },
  "llm": { "provider": "claude-code-cli" }
}
```

**Ollama (offline / no API key):**
```json
{
  "embedding": {
    "provider": "openai",
    "base_url": "http://localhost:11434/v1",
    "model": "nomic-embed-text"
  },
  "llm": { "provider": "claude-code-cli" }
}
```

The `llm` block is only needed for `research` mode. `search` works without it.

## Ollama + Docker

Run Ollama in Docker so ChunkHound can embed without any API key or local GPU setup. **ChunkHound itself must run natively** — it only supports stdio MCP transport, which Claude Code manages as a direct subprocess.

```bash
# Start Ollama in Docker
docker run -d \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  --name ollama \
  ollama/ollama

# Pull an embedding model (pick one):
docker exec -it ollama ollama pull nomic-embed-text          # 274MB, fast
docker exec -it ollama ollama pull mxbai-embed-large         # 669MB, better quality
docker exec -it ollama ollama pull dengcao/Qwen3-Embedding-8B:Q5_K_M  # 5.2GB, best local quality
```

Then configure ChunkHound to use it:
```json
{
  "embedding": {
    "provider": "openai",
    "base_url": "http://localhost:11434/v1",
    "model": "nomic-embed-text"
  },
  "llm": { "provider": "claude-code-cli" }
}
```

Ollama exposes an OpenAI-compatible API — ChunkHound uses the `openai` provider pointed at `localhost:11434`. No `api_key` needed (Ollama ignores it, but won't error if present).

**Verify Ollama is reachable:**
```bash
curl http://localhost:11434/api/tags | jq '.models[].name'
```

## Initial Index

```bash
# Auto-tune batch sizes for your hardware + provider
chunkhound calibrate

# Build the index (respects .gitignore)
chunkhound index
```

Large repos (50k files): expect 20–60 min on first index. Incremental updates are fast — only changed files are re-embedded.

## Wire MCP into Claude Code

```bash
claude mcp add ChunkHound chunkhound mcp
```

Or add a project-local `.mcp.json` in the repo root (committed to git, no path arg needed):
```json
{
  "mcpServers": {
    "ChunkHound": {
      "command": "chunkhound",
      "args": ["mcp"]
    }
  }
}
```

Or add to global `~/.claude/settings.json` (requires absolute path in `args`):
```json
{
  "mcpServers": {
    "ChunkHound": {
      "command": "chunkhound",
      "args": ["mcp", "/absolute/path/to/project"]
    }
  }
}
```

Run `chunkhound mcp --show-setup` to print all config formats for Claude Code, VS Code, and Cursor.

Claude Code starts the MCP server as a subprocess (stdio only — no HTTP mode). The index persists on disk between sessions — no separate server process needed.

## Commands

| Command | Purpose | Needs API key? |
|---------|---------|----------------|
| `chunkhound index` | Build/update the index | Embedding only |
| `chunkhound search "<query>"` | Semantic or regex search | Embedding only |
| `chunkhound research "<question>"` | Multi-hop analysis + synthesis | Embedding + LLM |
| `chunkhound calibrate` | Auto-tune batch sizes | Embedding only |
| `chunkhound diagnose` | Compare index vs git state | No |
| `chunkhound mcp` | Start MCP server (stdio) | Embedding only |

### `search` vs `research`

- **`search`** — fast, returns ranked code chunks matching the query. Use when you know what you're looking for.
- **`research`** — multi-hop exploration across the codebase, synthesizes a structured markdown report with line-number citations. Use for "how does X work" questions. Slower and costs LLM tokens.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Python 3.14+ installed | Use mise/pyenv to pin 3.13 |
| API key in `.chunkhound.json` committed to git | Use env var `CHUNKHOUND_EMBEDDING__API_KEY` or add to `.gitignore` |
| Upgrading from v3 → v4 without reindexing | v4 changed checksum algorithm — run `chunkhound index --full` |
| `research` returns nothing useful | Ensure `llm` block is configured; `research` silently degrades without it |
| MCP server not finding index | Run `chunkhound index` from the project root first |
| Trying to use HTTP transport / run in Docker | Stdio only — ChunkHound must run natively, not in a container |

## Exclude Patterns

```json
{
  "indexing": {
    "exclude": ["**/node_modules/**", "**/__pycache__/**", "**/dist/**", "**/*.min.js"]
  }
}
```

Patterns layer on top of `.gitignore` — you don't need to re-list gitignored paths.

## Project-Scoped Config

For team-shared projects, commit a `.chunkhound.json` without `api_key` fields:
```json
{
  "embedding": {
    "provider": "voyageai",
    "model": "voyage-3.5"
  },
  "llm": { "provider": "claude-code-cli" }
}
```
Each developer sets `CHUNKHOUND_EMBEDDING__API_KEY` in their shell env.
