import time
import asyncio
from typing import List, Dict, Tuple
from loguru import logger
from .base import RetrievalResult


class EnsembleRAG:
    """
    Runs Vector + BM25 keyword + Knowledge Graph + Web Search in parallel.
    Merges and re-ranks results by combined relevance score.
    Provides source provenance and confidence for every result.
    """

    def __init__(self, vector_store, llm_client, kg=None, web_search=None):
        self.vs = vector_store
        self.llm = llm_client
        self.kg = kg
        self.web_search = web_search

    # ── Vector search ──────────────────────────────────────────────────────
    def _vector_search(self, query: str, top_k: int = 8) -> List[Dict]:
        results = self.vs.search(query, top_k=top_k)
        for r in results:
            r["source_type"] = "vector"
            r["source_label"] = r.get("document", "Document")
        return results

    # ── BM25 keyword search (simple token overlap) ─────────────────────────
    def _bm25_search(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """Re-rank existing candidates using keyword overlap (no extra library)."""
        query_tokens = set(query.lower().split())
        stop = {"is", "are", "the", "a", "an", "in", "of", "to", "and", "or",
                "my", "i", "we", "can", "what", "does", "how", "for", "be"}
        query_tokens -= stop

        scored = []
        for c in candidates:
            text_tokens = set(c.get("text", "").lower().split())
            overlap = len(query_tokens & text_tokens)
            max_possible = max(len(query_tokens), 1)
            bm25_score = overlap / max_possible
            c["bm25_score"] = bm25_score
            c["combined_score"] = (c.get("score", 0) * 0.7) + (bm25_score * 0.3)
            scored.append(c)

        scored.sort(key=lambda x: x["combined_score"], reverse=True)
        return scored

    # ── Neo4j knowledge graph search ───────────────────────────────────────
    def _kg_search(self, query: str) -> List[Dict]:
        if not self.kg or not self.kg.enabled:
            return []
        try:
            # Find documents mentioning query keywords via graph
            keywords = [w for w in query.lower().split() if len(w) > 4][:3]
            results = []
            for kw in keywords:
                nodes = self.kg._run(
                    "MATCH (d:Document) WHERE toLower(d.name) CONTAINS $kw RETURN d LIMIT 3",
                    {"kw": kw}
                )
                for n in nodes:
                    doc = n.get("d", {})
                    results.append({
                        "text": f"Knowledge Graph: Document '{doc.get('name', '')}' is relevant to your query about {kw}.",
                        "document": doc.get("name", ""),
                        "doc_id": doc.get("id", ""),
                        "score": 0.65,
                        "source_type": "knowledge_graph",
                        "source_label": "Neo4j Knowledge Graph",
                        "chunk_index": 0,
                    })
            return results[:3]
        except Exception as e:
            logger.warning(f"KG search error: {e}")
            return []

    # ── Web search for real case law ───────────────────────────────────────
    async def _web_case_search(self, query: str) -> List[Dict]:
        if not self.web_search:
            return []
        try:
            # Search for real Indian case law related to query
            case_query = f"India court case judgment {query} site:indiankanoon.org OR site:supremecourt.gov.in"
            result = await self.web_search.search(case_query, max_results=3)
            if result and result != "Web search not available.":
                return [{
                    "text": result,
                    "document": "Web Search — Indian Case Law",
                    "doc_id": "web_case",
                    "score": 0.75,
                    "source_type": "web_case_law",
                    "source_label": "indiankanoon.org (Live Search)",
                    "chunk_index": 0,
                }]
        except Exception as e:
            logger.warning(f"Web case search error: {e}")
        return []

    # ── Web search for government advisories ──────────────────────────────
    async def _web_gov_search(self, query: str) -> List[Dict]:
        if not self.web_search:
            return []
        try:
            gov_query = f"India government law rule circular {query} site:pib.gov.in OR site:meity.gov.in OR site:rbi.org.in"
            result = await self.web_search.search(gov_query, max_results=2)
            if result and result != "Web search not available.":
                return [{
                    "text": result,
                    "document": "Government Advisory — PIB / Ministry",
                    "doc_id": "web_gov",
                    "score": 0.70,
                    "source_type": "web_government",
                    "source_label": "pib.gov.in / meity.gov.in (Live)",
                    "chunk_index": 0,
                }]
        except Exception as e:
            logger.warning(f"Web gov search error: {e}")
        return []

    # ── Main ensemble retrieval ────────────────────────────────────────────
    async def retrieve(self, query: str, top_k: int = 10) -> RetrievalResult:
        start = time.time()

        # 1. Run vector search
        vector_results = self._vector_search(query, top_k=top_k)

        # 2. BM25 re-ranking on top of vector results
        ranked_results = self._bm25_search(query, vector_results)

        # 3. Knowledge Graph search (parallel)
        # 4. Web case law search (parallel)
        # 5. Web government advisory search (parallel)
        kg_results, web_case, web_gov = await asyncio.gather(
            asyncio.to_thread(self._kg_search, query),
            self._web_case_search(query),
            self._web_gov_search(query),
        )

        # 6. Merge all sources
        all_results = ranked_results + kg_results + web_case + web_gov

        # 7. Deduplicate by document name (keep highest score)
        seen = {}
        for r in all_results:
            key = r.get("document", r.get("doc_id", ""))
            if key not in seen or r.get("combined_score", r.get("score", 0)) > seen[key].get("combined_score", seen[key].get("score", 0)):
                seen[key] = r

        final = sorted(seen.values(), key=lambda x: x.get("combined_score", x.get("score", 0)), reverse=True)
        final = final[:top_k]

        # Set source labels for display
        for r in final:
            if "source_type" not in r:
                r["source_type"] = "vector"
                r["source_label"] = r.get("document", "Document")

        confidence = final[0].get("combined_score", final[0].get("score", 0)) if final else 0.0

        logger.info(f"Ensemble RAG: {len(final)} results from vector({len(ranked_results)}), KG({len(kg_results)}), web({len(web_case)+len(web_gov)})")

        return RetrievalResult(
            chunks=final,
            strategy="ensemble_hybrid",
            confidence=confidence,
            time_ms=(time.time() - start) * 1000,
        )
