#!/usr/bin/env python3
import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quick viewer for local ChromaDB collections."
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
        "--limit",
        type=int,
        default=5,
        help="How many records to show (default: 5).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show documents and metadatas instead of peek summary.",
    )
    args = parser.parse_args()

    try:
        import chromadb  # type: ignore
    except Exception as exc:  # pragma: no cover - import error path
        print(f"chromadb import failed: {exc}", file=sys.stderr)
        return 2

    client = chromadb.PersistentClient(path=args.path)
    try:
        collection = client.get_collection(args.collection)
    except Exception as exc:
        print(f"failed to open collection '{args.collection}': {exc}", file=sys.stderr)
        return 3

    print(f"collection: {args.collection}")
    print(f"count: {collection.count()}")

    if args.full:
        data = collection.get(
            include=["documents", "metadatas"],
            limit=args.limit,
        )
        print(data)
    else:
        print(collection.peek())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
