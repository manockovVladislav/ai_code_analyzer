import os

try:
    import chromadb
except ImportError:
    chromadb = None


class CodeMemory:
    """Внешняя память для хранения чанков кода (ChromaDB или fallback)."""

    def __init__(self, collection_name: str = "code_memory"):
        """Создает память и готовит хранилище для чанков."""
        self.collection_name = collection_name
        self.persist_dir = os.path.join(os.path.dirname(__file__), "chroma_db")
        self._init_storage()

    def _init_storage(self):
        """Инициализирует ChromaDB или fallback-хранилище."""
        if chromadb is None:
            self.client = None
            self.collection = None
            self.fallback_chunks = []
            self.summary_items = []
            return
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        try:
            self.collection = self.client.get_or_create_collection(self.collection_name)
        except Exception:
            self.collection = self.client.get_collection(self.collection_name)
        self.fallback_chunks = []
        self.summary_items = []

    def _fake_embed(self, text: str) -> list[float]:
        """Возвращает фиктивный эмбеддинг для совместимости с ChromaDB."""
        return [0.0] * 128

    def store_chunks(self, file_path: str, lang: str, chunks: list[str], kind: str = "code"):
        """Сохраняет чанки кода в ChromaDB или локальный fallback."""
        if self.collection is None:
            for idx, chunk in enumerate(chunks):
                self.fallback_chunks.append(
                    {
                        "id": f"{file_path}:{idx}",
                        "lang": lang,
                        "text": chunk,
                        "kind": kind,
                    }
                )
            return
        for idx, chunk in enumerate(chunks):
            doc_id = f"{file_path}:{idx}"
            self.collection.add(
                documents=[chunk],
                embeddings=[self._fake_embed(chunk)],
                metadatas=[{"path": file_path, "lang": lang, "chunk": idx, "kind": kind}],
                ids=[doc_id],
            )

    def store_summary(self, scope: str, text: str, kind: str = "file_summary"):
        """Сохраняет краткий вывод (по файлу/блоку/проекту)."""
        if not text:
            return
        if self.collection is None:
            self.summary_items.append({"scope": scope, "kind": kind, "text": text})
            return
        doc_id = f"{kind}:{scope}:{len(self.summary_items)}"
        self.collection.add(
            documents=[text],
            embeddings=[self._fake_embed(text)],
            metadatas=[{"scope": scope, "kind": kind}],
            ids=[doc_id],
        )
        self.summary_items.append({"scope": scope, "kind": kind, "text": text})

    def get_recent_summaries(self, kind: str = "file_summary", limit: int = 5) -> list[str]:
        """Возвращает последние краткие выводы указанного типа."""
        results: list[str] = []
        for item in reversed(self.summary_items):
            if item.get("kind") == kind:
                results.append(item.get("text", ""))
                if len(results) >= limit:
                    break
        return list(reversed(results))

    def list_summaries(self, kind: str = "file_summary") -> list[dict]:
        """Возвращает все сохраненные выводы по типу."""
        return [item for item in self.summary_items if item.get("kind") == kind]

    def query(self, query_text: str, top_k: int = 3, kind: str | None = None) -> list[str]:
        """Возвращает наиболее релевантные чанки по текстовому запросу."""
        if self.collection is not None:
            try:
                embedding = self._fake_embed(query_text)
                where = {"kind": kind} if kind else None
                result = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=top_k,
                    include=["documents"],
                    where=where,
                )
                docs = result.get("documents", [])
                if docs:
                    return docs[0]
            except Exception:
                return []
        # Fallback: простой поиск по подстроке
        matches = []
        for item in self.fallback_chunks:
            if kind and item.get("kind") != kind:
                continue
            if query_text in item["text"]:
                matches.append(item["text"])
                if len(matches) >= top_k:
                    break
        return matches
