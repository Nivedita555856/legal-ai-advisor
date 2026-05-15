from typing import List, Dict
from loguru import logger

# CrewAI disabled - using direct Groq fallback for reliability
CREWAI_AVAILABLE = False


class CrewAgents:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.available = CREWAI_AVAILABLE
        if not self.available:
            logger.info("CrewAI disabled - using direct Groq fallback")

    async def analyze(self, query: str, documents: List[Dict], jurisdiction: str = "India", mcts_focus: str = None) -> Dict:
        """Analyze legal documents using direct Groq API (fallback mode)"""
        
        # Build context from documents
        context_parts = []
        for i, doc in enumerate(documents[:3]):
            text = doc.get("text", "")[:800]
            doc_name = doc.get("document", f"Document {i+1}")
            if text:
                context_parts.append(f"--- {doc_name} ---\n{text}")
        
        context = "\n\n".join(context_parts)
        
        if not context:
            context = "No specific documents found for this query."

        scenario_keywords = ["my ", "i ", "we ", "our ", "employer", "employee",
                             "terminated", "fired", "not paid", "breach", "dispute",
                             "violated", "what should i", "what can i", "can i sue"]
        is_scenario = any(kw in query.lower() for kw in scenario_keywords)

        # MCTS focus adds a specialized instruction
        mcts_instruction = ""
        if mcts_focus == "check_compliance":
            mcts_instruction = "\n4. Compliance check: does this comply with current Indian laws and regulations?"
        elif mcts_focus == "search_precedents":
            mcts_instruction = "\n4. Relevant legal precedents or similar case outcomes under Indian law"
        elif mcts_focus == "find_contradictions":
            mcts_instruction = "\n4. Any contradictions or inconsistencies found in the documents"

        risk_instruction = "3. Risk level (LOW, MEDIUM, HIGH, or CRITICAL)" if is_scenario else "3. Recommended next steps"

        prompt = f"""You are an expert Indian legal awareness advisor.
Write in plain English. Do not use asterisks, bold, emojis, or markdown.
Use numbered points and clear paragraphs only.

Query: {query}
Jurisdiction: {jurisdiction}

Relevant legal content:
{context}

Answer structured as:
1. DIRECT ANSWER: Answer immediately, citing the specific section/clause/article name.
2. LEGAL BASIS: Quote the exact law and section. E.g. "Section 27, Indian Contract Act 1872 states..."
3. CASE LAW: Name one relevant Supreme Court or High Court judgment. E.g. "In XYZ vs ABC (Year), the court held..."
4. ACTIONABLE STEP: Tell them exactly what to do. Be specific. E.g. "Call 1930", "File at cybercrime.gov.in", "Approach the Labour Commissioner".
5. WHERE TO VERIFY: Give one relevant link: indiankanoon.org, consumerhelpline.gov.in, cybercrime.gov.in, nalsa.gov.in, or the official government portal.
{risk_instruction}{mcts_instruction}

Plain text only. No markdown formatting. This is for informational purposes only, not legal advice."""

        try:
            answer = await self.llm.generate(prompt, temperature=0.1)
            return {
                "analysis": answer,
                "risk_assessment": "",
                "compliance": "",
                "similar_cases": "",
                "crew_output": answer
            }
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "analysis": f"Analysis temporarily unavailable. Please try again. Error: {str(e)[:100]}",
                "risk_assessment": "",
                "compliance": "",
                "similar_cases": "",
                "crew_output": ""
            }

    async def _fallback_analyze(self, query: str, documents: List[Dict], jurisdiction: str = "India", mcts_focus: str = None) -> Dict:
        return await self.analyze(query, documents, jurisdiction, mcts_focus)
