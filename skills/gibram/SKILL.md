---
name: gibram
description: Use when researching or writing across a large doc corpus, finding related prior work, tracing concept relationships across notes/ADRs/specs, or indexing a specific directory of markdown files into a local knowledge graph. Also use when the user says "set up gibram for [directory]".
---

# GibRAM

In-memory knowledge graph + vector search for doc-heavy research and writing. Fully local — runs on Docker + Ollama, no external API keys.

**Default port:** 6161 · **Extractor:** llama3.2 via Ollama · **Embedder:** nomic-embed-text (768-dim) · **License:** MIT · **MCP:** wired in `settings.json`

See `README.md` in this directory for the full conceptual rundown.

---

## Claude Setup Runbook

When asked to "set up gibram for [directory]", follow these steps in order using Bash. Stop and report if any step fails.

### Step 1 — Start gibram server (Docker)

```bash
# Check if already running
docker ps --filter name=gibram --format '{{.Names}}'

# If not running, start it
docker compose -f ~/.claude/skills/gibram/docker-compose.yml up -d

# Verify it started
sleep 2 && docker ps --filter name=gibram --format 'table {{.Names}}\t{{.Status}}'
```

### Step 2 — Check Ollama is running

```bash
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print('Ollama running,', len(d['models']), 'models')" 2>/dev/null || echo "ERROR: Ollama not running — start it first"
```

### Step 3 — Ensure required models are available

```bash
# Check for nomic-embed-text (embedder)
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; print('nomic-embed-text: OK' if any('nomic-embed-text' in m for m in models) else 'MISSING')"

# Pull if missing
ollama pull nomic-embed-text

# Check for llama3.2 (extractor) — or substitute your preferred model
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=[m['name'] for m in json.load(sys.stdin)['models']]; print('llama3.2: OK' if any('llama3.2' in m for m in models) else 'MISSING')"

ollama pull llama3.2
```

### Step 4 — Index the directory

Use the `index_directory` MCP tool (preferred), or fall back to the CLI script:

```bash
# CLI fallback only — prefer the MCP tool
uv run ~/.claude/skills/gibram/index-docs.py \
  --dir /path/to/docs \
  --session-id chosen-session-id
```

MCP tool call: `index_directory("/path/to/docs", "chosen-session-id")`

### Step 5 — Verify

```bash
# Confirm server health
curl -s http://localhost:6161  # should respond (even with error, not connection refused)
```

Then do a test query via MCP: `query_docs("test", "chosen-session-id", top_k=1)`

---

---

## MCP Tools

| Tool | Args | When to use |
|------|------|-------------|
| `query_docs` | `query, session_id, top_k=5` | Research, find related prior work, trace concept threads |
| `index_directory` | `path, session_id` | Seed a new corpus or refresh after doc changes |

**Use `top_k=10` or `top_k=20` for broad research** — default 5 is conservative.

---

## Session IDs (corpus namespaces)

One session per logical corpus. Same server, isolated graphs.

| Corpus | Suggested session_id |
|--------|---------------------|
| Obsidian work notes | `vault-work` |
| Project ADRs | `myproject-adrs` |
| Design specs | `myproject-specs` |

---

## Changing Models

Edit `~/.claude/skills/gibram/mcp-server.py` env vars or pass via MCP server config:

| Model | Dims | Notes |
|-------|------|-------|
| `nomic-embed-text` | 768 | Default embedder, good quality |
| `mxbai-embed-large` | 1024 | Higher quality, update `server-config.yaml` to `vector_dim: 1024` |
| `llama3.2` | — | Default extractor |
| `qwen2.5` | — | Alternative extractor, strong at structured extraction |

If you change the embedder model, update `vector_dim` in `server-config.yaml` and restart the container.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Connection refused on port 6161 | Run Step 1 — container not started |
| `ollama: connection refused` | Start Ollama app or `ollama serve` |
| `model not found` during indexing | Run `ollama pull <model>` |
| Empty query results | Re-index — data is ephemeral, lost on container restart |
| Wrong vector dimensions | `server-config.yaml` `vector_dim` must match embedder model |

---

## Promoting to a Plugin

When graduating this to a marketplace plugin, the MCP server registration moves into the plugin manifest. For manual wiring (local skills or new installs), add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "gibram": {
      "command": "uv",
      "args": ["run", "/path/to/skills/gibram/mcp-server.py"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434/v1",
        "GIBRAM_EXTRACTOR_MODEL": "llama3.2",
        "GIBRAM_EMBEDDER_MODEL": "nomic-embed-text"
      }
    }
  }
}
```

`/path/to/skills/gibram/` is wherever the skill directory lives in the plugin's file structure.

---

## CLI Indexer (direct use)

```bash
# Default (Ollama)
uv run ~/.claude/skills/gibram/index-docs.py \
  --dir ~/path/to/docs \
  --session-id my-corpus

# OpenAI fallback
OPENAI_API_KEY=sk-... uv run ~/.claude/skills/gibram/index-docs.py \
  --dir ~/path/to/docs \
  --session-id my-corpus \
  --openai
```
