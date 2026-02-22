#!/usr/bin/env python3
# /// script
# dependencies = ["gibram", "openai"]
# ///
"""Index a directory of markdown files into GibRAM using Ollama (default) or OpenAI.

Typical usage:
  # Fully local (Ollama extract + embed) — requires GibRAM configured for 768 dims
  uv run index-docs.py --dir ./sources --session-id my-corpus

  # Hybrid: Ollama extract, OpenAI embed (1536 dims = GibRAM default)
  OPENAI_API_KEY=sk-... uv run index-docs.py --dir ./sources --session-id my-corpus --openai-embed

  # Fully OpenAI
  OPENAI_API_KEY=sk-... uv run index-docs.py --dir ./sources --session-id my-corpus --openai
"""

import argparse
import os
import sys
from pathlib import Path

from openai import OpenAI
from gibram import GibRAMIndexer
from gibram.extractors import OpenAIExtractor
from gibram.embedders import OpenAIEmbedder

OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_EXTRACTOR_MODEL = "llama3.2"
DEFAULT_EMBEDDER_MODEL = "nomic-embed-text"


class OllamaExtractor(OpenAIExtractor):
    """OpenAIExtractor wired to a local Ollama endpoint."""

    def __init__(self, model: str, base_url: str = OLLAMA_BASE_URL) -> None:
        super().__init__(api_key="ollama", model=model)
        self.client = OpenAI(api_key="ollama", base_url=base_url)


class OllamaEmbedder(OpenAIEmbedder):
    """OpenAIEmbedder wired to a local Ollama endpoint.

    Overrides embed() to:
    - Truncate texts to ~6000 chars (nomic-embed-text has a 2048-token context window)
    - Omit the `dimensions` kwarg (Ollama doesn't support it)
    - Fall back to embedding individually if a batch triggers a context-length error
    """

    MAX_CHARS = 6000  # ~1500 tokens @ 4 chars/token

    def __init__(self, model: str, base_url: str = OLLAMA_BASE_URL) -> None:
        super().__init__(api_key="ollama", model=model)
        self.client = OpenAI(api_key="ollama", base_url=base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        truncated = [t[:self.MAX_CHARS] if t else t for t in texts]
        try:
            resp = self.client.embeddings.create(model=self.model, input=truncated)
            return [item.embedding for item in resp.data]
        except Exception as e:
            if len(truncated) == 1:
                raise
            print(f"  [embed] Batch of {len(truncated)} failed ({e}), retrying individually")
            result = []
            for text in truncated:
                try:
                    r = self.client.embeddings.create(model=self.model, input=[text])
                    result.append(r.data[0].embedding)
                except Exception as inner:
                    print(f"  [embed] Single embed failed, using zero vector: {inner}")
                    result.append([0.0] * 768)  # nomic-embed-text dim
            return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Index markdown docs into GibRAM")
    parser.add_argument("--dir", required=True, help="Directory to index")
    parser.add_argument("--session-id", required=True, help="GibRAM session namespace")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=6161)
    parser.add_argument("--batch-size", type=int, default=50)
    # Ollama options (default)
    parser.add_argument("--ollama-url", default=OLLAMA_BASE_URL, help="Ollama base URL")
    parser.add_argument("--extractor-model", default=DEFAULT_EXTRACTOR_MODEL)
    parser.add_argument("--embedder-model", default=DEFAULT_EMBEDDER_MODEL)
    # Backend options
    parser.add_argument("--openai", action="store_true",
                        help="Use OpenAI for both extraction and embedding (requires OPENAI_API_KEY)")
    parser.add_argument("--openai-embed", action="store_true",
                        help="Use Ollama for extraction but OpenAI text-embedding-3-small for embedding "
                             "(1536 dims — compatible with GibRAM default config; requires OPENAI_API_KEY)")
    args = parser.parse_args()

    docs_dir = Path(args.dir).expanduser().resolve()
    if not docs_dir.exists():
        print(f"Error: Directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(docs_dir.rglob("*.md"))
    if not md_files:
        print(f"No markdown files found in {docs_dir}")
        sys.exit(0)

    api_key: str | None = None
    if args.openai or args.openai_embed:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY required with --openai / --openai-embed", file=sys.stderr)
            sys.exit(1)

    if args.openai:
        extractor = OpenAIExtractor(model="gpt-4o", api_key=api_key)
        embedder = OpenAIEmbedder(model="text-embedding-3-small", api_key=api_key)
        backend = "OpenAI (gpt-4o + text-embedding-3-small)"
    elif args.openai_embed:
        extractor = OllamaExtractor(model=args.extractor_model, base_url=args.ollama_url)
        embedder = OpenAIEmbedder(model="text-embedding-3-small", api_key=api_key)
        backend = f"Hybrid (Ollama {args.extractor_model} + OpenAI text-embedding-3-small)"
    else:
        extractor = OllamaExtractor(model=args.extractor_model, base_url=args.ollama_url)
        embedder = OllamaEmbedder(model=args.embedder_model, base_url=args.ollama_url)
        backend = f"Ollama ({args.extractor_model} / {args.embedder_model})"

    print(f"Found {len(md_files)} markdown files in {docs_dir}")
    print(f"Session:  {args.session_id} → {args.host}:{args.port}")
    print(f"Backend:  {backend}\n")

    indexer = GibRAMIndexer(
        session_id=args.session_id,
        host=args.host,
        port=args.port,
        extractor=extractor,
        embedder=embedder,
    )

    total_entities = 0
    total_relationships = 0
    batch: list[str] = []

    for i, path in enumerate(md_files, 1):
        try:
            batch.append(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  Skipped {path.name}: {e}")

        if len(batch) >= args.batch_size or i == len(md_files):
            if batch:
                stats = indexer.index_documents(batch)
                total_entities += stats.entities_extracted
                total_relationships += stats.relationships_extracted
                print(
                    f"  [{i}/{len(md_files)}] "
                    f"+{stats.entities_extracted} entities, "
                    f"+{stats.relationships_extracted} relationships"
                )
                batch = []

    print(f"\nDone.")
    print(f"  Total entities:      {total_entities}")
    print(f"  Total relationships: {total_relationships}")
    print(f"  Session ID:          {args.session_id}")


if __name__ == "__main__":
    main()
