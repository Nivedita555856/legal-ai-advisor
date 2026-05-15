from .base import BaseRAG, RetrievalResult
import time


class ParentChildRAG(BaseRAG):
    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        start = time.time()
        k = top_k or 20
        children = self.vector_store.search(query, top_k=k)
        parent_map = {}
        for r in children:
            doc_id = r.get("doc_id", "")
            chunk_idx = r.get("chunk_index", 0)
            key = f"{doc_id}_{chunk_idx // 5}"
            if key not in parent_map or parent_map[key]["score"] < r["score"]:
                parent_map[key] = {
                    "text": r.get("text", ""), "score": r["score"],
                    "document": r.get("document", ""), "doc_id": doc_id,
                }
        parents = sorted(parent_map.values(), key=lambda x: x["score"], reverse=True)
        return RetrievalResult(
            chunks=parents[:self.top_k],
            strategy="parent_child",
            confidence=parents[0]["score"] if parents else 0.0,
            time_ms=(time.time() - start) * 1000,
        )
