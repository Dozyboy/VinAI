from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            client = chromadb.Client()
            self._collection = client.create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Tạo một bản ghi chuẩn hóa cho bộ nhớ in-memory."""
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": doc.metadata,
            "embedding": self._embedding_fn(doc.content)
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Tìm kiếm tương đồng (In-memory) dựa trên Dot Product / Cosine Similarity."""
        query_emb = self._embedding_fn(query)
        scored_records = []
        
        for record in records:
            score = _dot(query_emb, record["embedding"])
            scored_records.append((score, record))
            
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, record in scored_records[:top_k]:
            result_copy = record.copy()
            result_copy["score"] = score
            results.append(result_copy)
            
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        if not docs:
            return

        if self._use_chroma:
            ids = [doc.id for doc in docs]
            documents = [doc.content for doc in docs]
            metadatas = [doc.metadata for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            for doc in docs:
                self._store.append(self._make_record(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        if self._use_chroma:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k
            )
            
            results = []
            if res.get("ids") and res["ids"][0]:
                for i in range(len(res["ids"][0])):
                    results.append({
                        "id": res["ids"][0][i],
                        "content": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i] if res["metadatas"] else {},
                        "score": res["distances"][0][i] if res["distances"] else 0.0
                    })
            return results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=metadata_filter
            )
            
            results = []
            if res.get("ids") and res["ids"][0]:
                for i in range(len(res["ids"][0])):
                    results.append({
                        "id": res["ids"][0][i],
                        "content": res["documents"][0][i],
                        "metadata": res["metadatas"][0][i] if res["metadatas"] else {},
                        "score": res["distances"][0][i] if res["distances"] else 0.0
                    })
            return results
        else:
            filtered_records = []
            for record in self._store:
                match = True
                for k, v in metadata_filter.items():
                    if record.get("metadata", {}).get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
                    
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.
        Returns True if any chunks were removed, False otherwise.
        """
        initial_size = self.get_collection_size()
        
        if self._use_chroma:
            self._collection.delete(ids=[doc_id])
        else:
            self._store = [
                r for r in self._store 
                if r.get("id") != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
            ]
            
        return self.get_collection_size() < initial_size