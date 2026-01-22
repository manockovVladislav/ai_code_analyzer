#!/usr/bin/env python3
import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dump ChromaDB collection to a JSON file."
    )
    parser.add_argument(
        "--path",
        default="chroma_db",
        help="Path to ChromaDB persist directory (default: chroma_db).",
    )
    parser.add_argument(
        "--collection",
        default="code_memory",
        help="Collection name (default: code_memory).",
    )
    parser.add_argument(
        "--out",
        default="chroma_dump.json",
        help="Output JSON file (default: chroma_dump.json).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for how many records to dump.",
    )
    args = parser.parse_args()

    try:
        import chromadb  # type: ignore
    except Exception as exc:
        print(f"chromadb import failed: {exc}", file=sys.stderr)
        return 2

    client = chromadb.PersistentClient(path=args.path)
    try:
        collection = client.get_collection(args.collection)
    except Exception as exc:
        print(f"failed to open collection '{args.collection}': {exc}", file=sys.stderr)
        return 3

    try:
        data = collection.get(
            include=["documents", "metadatas"],
            limit=args.limit,
        )
    except Exception as exc:
        print(f"failed to fetch collection data: {exc}", file=sys.stderr)
        return 4

    payload = {
        "collection": args.collection,
        "count": collection.count(),
        "data": data,
    }
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2)
    except Exception as exc:
        print(f"failed to write '{args.out}': {exc}", file=sys.stderr)
        return 5

    print(f"dumped to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
