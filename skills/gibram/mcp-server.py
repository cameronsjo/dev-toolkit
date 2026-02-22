#!/usr/bin/env python3
# /// script
# dependencies = ["fastmcp", "gibram"]
# ///
"""GibRAM MCP server — query and index tools for Claude sessions.

Defaults to Ollama for local, private operation.
Set GIBRAM_BACKEND=openai to use OpenAI instead (requires OPENAI_API_KEY).
"""

import os
from pathlib import Path

from fastmcp import FastMCP
from gibram import GibRAMIndexer
from gibram.extractors import OpenAIExtractor
from gibram.embedders import OpenAIEmbedder

mcp = FastMCP("gibram")

GIBRAM_HOST = os.environ.get("GIBRAM_HOST", "localhost")
GIBRAM_PORT = int(os.environ.get("GIBRAM_PORT", "6161"))
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
EXTRACTOR_MODEL = os.environ.get("GIBRAM_EXTRACTOR_MODEL", "llama3.2")
EMBEDDER_MODEL = os.environ.get("GIBRAM_EMBEDDER_MODEL", "nomic-embed-text")
USE_OPENAI = os.environ.get("GIBRAM_BACKEND", "ollama").lower() == "openai"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def _indexer(session_id: str) -> GibRAMIndexer:
    if USE_OPENAI:
        extractor = OpenAIExtractor(model="gpt-4o", api_key=OPENAI_API_KEY)
        embedder = OpenAIEmbedder(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
    else:
        extractor = OpenAIExtractor(
            model=EXTRACTOR_MODEL,
            api_key="ollama",
            base_url=OLLAMA_BASE_URL,
        )
        embedder = OpenAIEmbedder(
            model=EMBEDDER_MODEL,
            api_key="ollama",
            base_url=OLLAMA_BASE_URL,
        )
    return GibRAMIndexer(
        session_id=session_id,
        host=GIBRAM_HOST,
        port=GIBRAM_PORT,
        extractor=extractor,
        embedder=embedder,
    )


@mcp.tool()
def query_docs(query: str, session_id: str, top_k: int = 5) -> str:
    """Query the GibRAM knowledge graph for entities related to a question.

    Returns entities ranked by combined vector similarity + graph traversal score.
    Use when researching a topic across indexed docs, finding prior decisions,
    or tracing how concepts connect across a document corpus.

    Args:
        query: Natural language question or topic to search for.
        session_id: The corpus namespace to query (set when indexing).
        top_k: Number of top entities to return. Default 5; use 10-20 for broad research.
    """
    indexer = _indexer(session_id)
    results = indexer.query(query, top_k=top_k)

    if not results.entities:
        return f"No results found for: {query!r} in session {session_id!r}"

    lines = [f"Query: {query}", f"Session: {session_id}", ""]
    for i, entity in enumerate(results.entities, 1):
        lines.append(f"{i}. {entity.title}  (score: {entity.score:.3f})")
        if hasattr(entity, "description") and entity.description:
            lines.append(f"   {entity.description}")

    return "\n".join(lines)


@mcp.tool()
def index_directory(path: str, session_id: str) -> str:
    """Index all markdown files in a directory into GibRAM.

    Walks the directory recursively and indexes every .md file.
    Use before querying a new corpus, or to refresh after doc changes.
    Indexing calls the LLM (Ollama by default) once per chunk — may take a few minutes
    for large directories.

    Args:
        path: Absolute path to the directory to index.
        session_id: Namespace for this corpus. Use the same ID when querying.
    """
    docs_dir = Path(path).expanduser().resolve()
    if not docs_dir.exists():
        return f"Error: Directory not found: {path}"

    md_files = sorted(docs_dir.rglob("*.md"))
    if not md_files:
        return f"No markdown files found in {path}"

    indexer = _indexer(session_id)
    docs: list[str] = []
    skipped = 0

    for p in md_files:
        try:
            docs.append(p.read_text(encoding="utf-8"))
        except Exception:
            skipped += 1

    stats = indexer.index_documents(docs)

    lines = [
        f"Indexed {len(docs)} files from {path}",
        f"Session:       {session_id}",
        f"Entities:      {stats.entities_extracted}",
        f"Relationships: {stats.relationships_extracted}",
    ]
    if skipped:
        lines.append(f"Skipped:       {skipped} unreadable files")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
