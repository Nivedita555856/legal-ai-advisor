from .base import BaseRAG, RetrievalResult
import time


class CorrectiveRAG(BaseRAG):
    def __init__(self, vector_store, llm_client, web_search=None):
        super().__init__(vector_store, llm_client)
        self.web_search = web_search
        self.fallback_threshold = 0.6

    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        start = time.time()
        k = top_k or self.top_k
        results = self.vector_store.search(query, top_k=k)
        avg = sum(r["score"] for r in results) / len(results) if results else 0
        if avg >= self.fallback_threshold:
            return RetrievalResult(
                chunks=results[:self.top_k], strategy="corrective",
                confidence=avg, time_ms=(time.time() - start) * 1000,
            )
        web_text = ""
        if self.web_search:
            try:
                web_text = await self.web_search.search(query)
            except Exception:
                web_text = "Web search unavailable."
        return RetrievalResult(
            chunks=[{"text": web_text or "No results.", "document": "Web Search", "score": 0.5, "source": "web"}],
            strategy="corrective_fallback",
            confidence=0.5,
            time_ms=(time.time() - start) * 1000,
        )
