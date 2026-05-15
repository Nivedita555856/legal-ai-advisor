from .base import BaseRAG, RetrievalResult
from prompts.templates import LegalPrompts
import time
import json


class SelfRAG(BaseRAG):
    async def retrieve(self, query: str, top_k: int = None) -> RetrievalResult:
        start = time.time()
        k = (top_k or self.top_k) * 2
        initial = self.vector_store.search(query, top_k=k)
        scored = []
        for doc in initial:
            try:
                prompt = LegalPrompts.self_reflection_prompt(query, [doc.get("text", "")])
                raw = await self.llm.generate(prompt, temperature=0)
                s = raw.find("{"); e = raw.rfind("}") + 1
                data = json.loads(raw[s:e]) if s >= 0 else {}
                if data.get("has_answer", False):
                    doc["self_score"] = data.get("confidence", 0.5)
                    scored.append(doc)
            except Exception:
                pass
        scored.sort(key=lambda x: x.get("self_score", 0), reverse=True)
        final = scored[:self.top_k] or initial[:self.top_k]
        return RetrievalResult(
            chunks=final,
            strategy="self_rag",
            confidence=final[0].get("self_score", final[0].get("score", 0)) if final else 0.0,
            time_ms=(time.time() - start) * 1000,
        )
