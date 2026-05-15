from .base import BaseRAG, RetrievalResult
from prompts.templates import LegalPrompts
import time


class HyDERAG(BaseRAG):
    """Hypothetical Document Embeddings — generates a hypothetical answer first."""

    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        start = time.time()
        k = top_k or self.top_k
        hypo_prompt = LegalPrompts.hyde_prompt(query)
        hypo_response = await self.llm.generate(hypo_prompt, temperature=0.3)
        results = self.vector_store.search(hypo_response, top_k=k)
        filtered = self._filter_results(results)
        return RetrievalResult(
            chunks=filtered,
            strategy="hyde",
            confidence=filtered[0]["score"] if filtered else 0.0,
            time_ms=(time.time() - start) * 1000,
        )
