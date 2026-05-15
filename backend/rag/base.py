from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import time

@dataclass
class RetrievalResult:
    chunks: List[Dict]
    strategy: str
    confidence: float
    time_ms: float

class BaseRAG(ABC):
    def __init__(self, vector_store, llm_client):
        self.vector_store = vector_store
        self.llm = llm_client
        self.top_k = 10
        self.threshold = 0.7

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        pass

    def _filter_results(self, results: List[Dict]) -> List[Dict]:
        return [r for r in results if r.get("score", 0) >= self.threshold]
