from typing import List, Tuple
from .vector_rag import VectorRAG
from .ensemble_rag import EnsembleRAG
from .base import RetrievalResult


class RAGRouter:
    """
    Routes queries through the Ensemble RAG (Vector + BM25 + KG + Web).
    Falls back to pure vector search if ensemble is unavailable.
    """

    def __init__(self, vector_store=None, llm_client=None, web_search=None, kg=None):
        self.vector_store = vector_store
        self.llm = llm_client
        self._web_search = web_search
        self._kg = kg
        self._ensemble = None
        self._vector = None

    def _init(self):
        if not self.vector_store or not self.llm:
            return
        if self._ensemble is None:
            self._ensemble = EnsembleRAG(
                vector_store=self.vector_store,
                llm_client=self.llm,
                kg=self._kg,
                web_search=self._web_search,
            )
        if self._vector is None:
            self._vector = VectorRAG(self.vector_store, self.llm)

    async def route(self, query: str, confidence: float = None) -> Tuple[object, RetrievalResult]:
        """Always uses Ensemble RAG for maximum coverage."""
        self._init()
        if not self._ensemble:
            return None, RetrievalResult(chunks=[], strategy="none", confidence=0.0, time_ms=0.0)
        result = await self._ensemble.retrieve(query)
        return self._ensemble, result

    async def ensemble(self, query: str) -> List[RetrievalResult]:
        """Run full ensemble and return all results."""
        self._init()
        if not self._ensemble:
            return []
        result = await self._ensemble.retrieve(query)
        return [result]
