# GibRAM — Knowledge Graph RAG for Docs

**Date:** 2026-02-19 · **Scope:** Conceptual reference + Claude integration

---

## What It Is

GibRAM (**Graph in-Buffer Retrieval & Associative Memory**) is an in-memory knowledge graph server. It stores documents, the entities and relationships extracted from them, and vector embeddings for all of the above — held entirely in RAM.

It's a server (port 6161 by default) that you run locally. A Python SDK and the included MCP server let Claude interact with it during sessions.

---

## How It Works

### Indexing pipeline

When you feed GibRAM a document, it runs a three-stage pipeline:

```
Document text
     │
     ▼
  Chunker          → splits text into overlapping TextUnits (default: token windows)
     │
     ▼
  Extractor        → LLM reads each chunk, pulls out entities and relationships
     │              ("Guido van Rossum" — CREATED → "Python")
     ▼
  Embedder         → vector embedding for each entity
     │
     ▼
  Graph store      → entity nodes + relationship edges + embeddings, all in RAM
```

The result is a graph where **concepts are nodes** and **how they relate is the edges**.

### Query pipeline

When you query GibRAM:

1. Your query gets embedded into a vector
2. **Vector search** finds entities with similar embeddings — semantically similar content
3. **Graph traversal** follows relationship edges outward from those entities (k hops)
4. Results are ranked by combined similarity + graph proximity score and returned

---

## What It Solves

Plain vector search answers: *"What chunks are textually similar to this query?"*

GibRAM answers: *"What entities are related to this query, and what else are they connected to?"*

### Example

You index a set of ADRs. One ADR is titled "Use JWT for stateless auth." It mentions OAuth, session management, and references two other ADRs.

| Query: "authentication decisions" | Vector Search | GibRAM |
|---|---|---|
| Returns JWT ADR | ✓ | ✓ |
| Returns OAuth ADR | Only if "OAuth" appears near "authentication" | ✓ — linked via `REFERENCES` relationship |
| Returns session ADR | Only if text is similar | ✓ — linked via `CONTRADICTS` relationship |
| Shows the chain between them | ✗ | ✓ |

The graph traversal surfaces context that's *related* even when the text isn't directly similar.

---

## What It's Good At

- **Research across large note collections** — follow threads across dozens of connected docs
- **Finding prior decisions** — "what was decided about X, and what led to it?"
- **Writing with full context** — surface all docs that relate to what you're about to write
- **Concept mapping** — see how ideas connect across a corpus, not just individual documents

---

## What It's Not Good At

- **Code navigation** — the extractor is NLP-based (entity/relationship in prose), not AST-aware
- **Small/known file sets** — if you can just read the files, do that; GibRAM adds overhead
- **Real-time data** — it's a snapshot; you re-index when docs change
- **Precision queries** — graph traversal casts a wide net; if you need exact matches, use grep
- **Long-term persistence** — data lives in RAM; server restart = data gone (unless WAL/BGSAVE configured)

---

## Key Concepts

### Session ID
Every indexed corpus lives under a `session_id`. This is a namespace — the same gibram-server can hold multiple independent graphs. Use one session per logical corpus:

| Corpus | session_id |
|--------|------------|
| Work vault notes | `vault-work` |
| Project ADRs | `myproject-adrs` |
| Design specs | `myproject-specs` |

### Ephemeral by Design
GibRAM is intentionally in-memory. It's built for session-scoped analysis, not as a database. If you restart the server, you re-index. This is a feature: stale context can't accumulate silently.

### Pluggable Pipeline
Chunker, extractor, and embedder are all swappable. The defaults use OpenAI. You can replace any of the three independently — e.g., use a custom chunker that respects markdown headers while keeping the default extractor.

---

## Architecture (this integration)

```
Your docs directory
       │
       ▼
  index-docs.py              ← CLI script, run once or on change
  (or index_directory MCP)
       │
       ▼
  gibram-server :6161        ← always-on local server (binary or Docker)
       │
       ▼
  mcp-server.py              ← Claude Code MCP integration
       │
       ▼
  Claude session             ← query_docs / index_directory tools available
```

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude skill — setup, quick reference, MCP registration |
| `README.md` | This file — conceptual rundown |
| `mcp-server.py` | MCP server exposing `query_docs` and `index_directory` tools |
| `index-docs.py` | CLI indexer for seeding/refreshing a corpus |

---

## MCP Tools (for Claude)

### `query_docs(query, session_id, top_k=5)`
Query the knowledge graph. Returns entities ranked by semantic + graph score.

**When to call:** Whenever researching a topic, looking for prior decisions, or trying to understand how concepts connect across a corpus.

### `index_directory(path, session_id)`
Index all `.md` files in a directory tree into GibRAM.

**When to call:** Before the first query on a new corpus, or after significant doc changes.

---

## Limitations & Gotchas

- **OPENAI_API_KEY required** — the default extractor calls the OpenAI API during indexing. Querying does not re-call the API.
- **Index cost** — indexing calls the LLM once per chunk. Large corpora = real API cost. Do it once, query many times.
- **Graph quality = extractor quality** — the relationships GibRAM finds are only as good as what the LLM extracts. Dense technical prose extracts better than bullet lists or code snippets.
- **Top-k is shallow** — default `top_k=5` returns 5 entities. For broad research tasks, use `top_k=10` or `top_k=20`.
- **No incremental indexing** — re-indexing a session replaces it. If you add new docs, re-index the whole directory.
