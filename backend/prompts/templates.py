class LegalPrompts:

    SYSTEM_PROMPT = """You are an expert Indian legal document analyst.
Answer based strictly on provided documents. Cite sections, clauses, and document names.
If information is missing, say so clearly. Never hallucinate."""

    @staticmethod
    def qa_prompt(query: str, context: str) -> str:
        return f"""Context from legal documents:
{context}

Question: {query}

Provide:
1. Direct answer with citations
2. Relevant sections/clauses
3. Risk level if applicable (LOW / MEDIUM / HIGH / CRITICAL)
4. Recommended action

Answer:"""

    @staticmethod
    def hyde_prompt(query: str) -> str:
        return f"""Generate a hypothetical legal document excerpt that would answer this query.
Query: {query}
Write a realistic legal clause (2-3 sentences) containing the answer.
Hypothetical excerpt:"""

    @staticmethod
    def self_reflection_prompt(query: str, docs: list) -> str:
        return f"""Evaluate if these documents answer the query.
Query: {query}
Documents: {docs[:3]}
Return JSON only: {{"has_answer": true, "confidence": 0.85, "missing": []}}"""
