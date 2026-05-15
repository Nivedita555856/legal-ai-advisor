from typing import List, Dict
from loguru import logger

# AutoGen fully disabled - using direct Groq for reliability
logger.info("AutoGen disabled - using direct Groq analysis")


class AutoGenAgents:
    """Legal analysis using direct Groq LLM (AutoGen disabled for token safety)."""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def analyze(self, query: str, documents: List[Dict], deep: bool = False) -> Dict:
        """Analyze legal documents. deep=True when MCTS recommends deeper clause extraction."""
        max_docs = 3 if deep else 2
        max_chars = 600 if deep else 400

        context = "\n\n".join([
            f"[{d.get('document', 'Doc')}]\n{d.get('text', '')[:max_chars]}"
            for d in documents[:max_docs]
        ])
        if not context.strip():
            context = "No documents retrieved."

        scenario_keywords = ["my ", "i ", "we ", "our ", "employer", "employee",
                             "terminated", "fired", "not paid", "breach", "dispute",
                             "violated", "what should i", "what can i", "can i sue"]
        is_scenario = any(kw in query.lower() for kw in scenario_keywords)

        extra = ""
        if deep:
            extra = "\n4. All parties and their obligations\n5. Key dates and deadlines"
        risk_line = "3. Risk level (LOW, MEDIUM, HIGH, or CRITICAL)" if is_scenario else "3. Recommended action"

        prompt = f"""You are an Indian legal document analyst.
Write in plain English. Do not use asterisks, bold text, bullet symbols, or emojis.
Use numbered points and clear paragraphs only.

Query: {query}

Document excerpts:
{context}

Provide:
1. Direct answer citing the specific clause or section by name
2. What the document or law says about this
{risk_line}{extra}

Plain text answer only:"""
        try:
            answer = await self.llm.generate(prompt, max_tokens=1024)
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            answer = "Analysis unavailable. Please try again."

        return {
            "summary": answer,
            "extracted": "",
            "critique": "",
            "debate": None,
            "agents_used": ["groq_direct" if not deep else "groq_deep"],
        }

    async def _fallback_analyze(self, query: str, documents: List[Dict]) -> Dict:
        return await self.analyze(query, documents)
