#!/usr/bin/env python3
"""
Tax Document RAG
Upload your tax PDFs once, then ask questions across all of them.

Usage:
  python tax_rag.py ingest path/to/docs/         # index a folder of PDFs
  python tax_rag.py ingest 2023_taxes.pdf        # index a single PDF
  python tax_rag.py ask "What was my total income in 2023?"
  python tax_rag.py list                         # show indexed documents
  python tax_rag.py clear                        # wipe the index
"""

import sys
import os
import re
import argparse
import anthropic
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from pathlib import Path

DB_PATH = os.path.expanduser("~/.tax_rag_db")
COLLECTION_NAME = "tax_documents"
CHUNK_SIZE = 600       # words per chunk
CHUNK_OVERLAP = 80     # words of overlap between chunks
TOP_K = 8              # chunks to retrieve per query
EMBED_MODEL = "all-MiniLM-L6-v2"


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=ef)


def extract_text(pdf_path: str, password: str = "") -> str:
    reader = PdfReader(pdf_path)
    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == 0:
            raise ValueError(f"Wrong password for {Path(pdf_path).name}")
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages)


def chunk_text(text: str, source: str) -> list[dict]:
    words = text.split()
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for i in range(0, len(words), step):
        chunk_words = words[i : i + CHUNK_SIZE]
        if len(chunk_words) < 20:
            break
        chunks.append({
            "text": " ".join(chunk_words),
            "source": source,
            "chunk_index": len(chunks),
        })
    return chunks


def ingest(path: str, password: str = ""):
    collection = get_collection()
    pdf_paths = []

    p = Path(path)
    if p.is_dir():
        pdf_paths = list(p.glob("**/*.pdf")) + list(p.glob("**/*.PDF"))
    elif p.suffix.lower() == ".pdf":
        pdf_paths = [p]
    else:
        print(f"Error: {path} is not a PDF or directory")
        sys.exit(1)

    if not pdf_paths:
        print(f"No PDFs found in {path}")
        return

    for pdf_path in pdf_paths:
        source = str(pdf_path)
        # Check if already indexed
        existing = collection.get(where={"source": source})
        if existing["ids"]:
            print(f"  Already indexed: {pdf_path.name} ({len(existing['ids'])} chunks) — skipping")
            continue

        print(f"  Indexing: {pdf_path.name}...", end=" ", flush=True)
        try:
            text = extract_text(source, password)
        except ValueError as e:
            print(f"ERROR: {e}")
            continue
        if not text.strip():
            print("no text extracted, skipping")
            continue

        chunks = chunk_text(text, source)
        ids = [f"{source}::chunk{c['chunk_index']}" for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"{len(chunks)} chunks")

    total = collection.count()
    print(f"\nIndex now contains {total} total chunks.")


def ask(question: str):
    collection = get_collection()
    if collection.count() == 0:
        print("No documents indexed yet. Run: python tax_rag.py ingest <path>")
        sys.exit(1)

    results = collection.query(query_texts=[question], n_results=min(TOP_K, collection.count()))
    chunks = results["documents"][0]
    metas = results["metadatas"][0]

    # Build context with source attribution
    context_parts = []
    seen_sources = set()
    for chunk, meta in zip(chunks, metas):
        source_name = Path(meta["source"]).name
        seen_sources.add(source_name)
        context_parts.append(f"--- From: {source_name} ---\n{chunk}")
    context = "\n\n".join(context_parts)

    sources_list = ", ".join(sorted(seen_sources))

    claude = anthropic.Anthropic()
    response = claude.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=(
            "You are a helpful tax document assistant. The user has provided excerpts from "
            "their personal tax documents. Answer questions accurately based only on the "
            "provided context. If the answer isn't in the context, say so clearly. "
            "Cite which document (filename) your answer comes from when relevant."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here are relevant excerpts from my tax documents:\n\n{context}\n\n"
                    f"Question: {question}"
                ),
            }
        ],
    )

    print()
    for block in response.content:
        if block.type == "text":
            print(block.text)

    print(f"\n(Sources searched: {sources_list})")


def list_docs():
    collection = get_collection()
    if collection.count() == 0:
        print("No documents indexed.")
        return

    all_items = collection.get()
    sources = {}
    for meta in all_items["metadatas"]:
        src = meta["source"]
        sources[src] = sources.get(src, 0) + 1

    print(f"Indexed documents ({len(sources)} files, {collection.count()} total chunks):\n")
    for src, count in sorted(sources.items()):
        print(f"  {Path(src).name:50s}  {count} chunks")


def clear():
    import shutil
    if Path(DB_PATH).exists():
        shutil.rmtree(DB_PATH)
        print("Index cleared.")
    else:
        print("Nothing to clear.")


def main():
    parser = argparse.ArgumentParser(description="Tax Document RAG")
    subparsers = parser.add_subparsers(dest="command")

    ingest_p = subparsers.add_parser("ingest", help="Index PDF files")
    ingest_p.add_argument("path", help="PDF file or folder of PDFs")
    ingest_p.add_argument("--password", default="", help="Password for encrypted PDFs")

    ask_p = subparsers.add_parser("ask", help="Ask a question")
    ask_p.add_argument("question", help="Your question")

    subparsers.add_parser("list", help="List indexed documents")
    subparsers.add_parser("clear", help="Clear the index")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest(args.path, args.password)
    elif args.command == "ask":
        ask(args.question)
    elif args.command == "list":
        list_docs()
    elif args.command == "clear":
        clear()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
