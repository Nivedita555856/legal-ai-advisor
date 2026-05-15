from .base import BaseRAG, RetrievalResult
import time


class VectorRAG(BaseRAG):
    """Standard vector similarity search."""

    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        start = time.time()
        k = top_k or self.top_k
        results = self.vector_store.search(query, top_k=k)
        filtered = self._filter_results(results)
        return RetrievalResult(
            chunks=filtered,
            strategy="vector",
            confidence=filtered[0]["score"] if filtered else 0.0,
            time_ms=(time.time() - start) * 1000,
        )
