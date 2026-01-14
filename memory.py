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
            return
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.create_collection(self.collection_name)
        self.fallback_chunks = []

    def _fake_embed(self, text: str) -> list[float]:
        """Возвращает фиктивный эмбеддинг для совместимости с ChromaDB."""
        return [0.0] * 128

    def store_chunks(self, file_path: str, lang: str, chunks: list[str]):
        """Сохраняет чанки кода в ChromaDB или локальный fallback."""
        if self.collection is None:
            for idx, chunk in enumerate(chunks):
                self.fallback_chunks.append(
                    {"id": f"{file_path}:{idx}", "lang": lang, "text": chunk}
                )
            return
        for idx, chunk in enumerate(chunks):
            doc_id = f"{file_path}:{idx}"
            self.collection.add(
                documents=[chunk],
                embeddings=[self._fake_embed(chunk)],
                metadatas=[{"path": file_path, "lang": lang, "chunk": idx}],
                ids=[doc_id],
            )

    def query(self, query_text: str, top_k: int = 3) -> list[str]:
        """Возвращает наиболее релевантные чанки по текстовому запросу."""
        if self.collection is not None:
            try:
                embedding = self._fake_embed(query_text)
                result = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=top_k,
                    include=["documents"],
                )
                docs = result.get("documents", [])
                if docs:
                    return docs[0]
            except Exception:
                return []
        # Fallback: простой поиск по подстроке
        matches = []
        for item in self.fallback_chunks:
            if query_text in item["text"]:
                matches.append(item["text"])
                if len(matches) >= top_k:
                    break
        return matches
