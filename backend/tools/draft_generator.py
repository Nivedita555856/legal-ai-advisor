from typing import List, Dict, Optional
from loguru import logger
from prompts.templates import LegalPrompts


class DraftGenerator:
    """Generate legal draft documents using LLM."""

    TEMPLATES = {
        "nda": "Non-Disclosure Agreement",
        "employment": "Employment Agreement",
        "notice": "Legal Notice",
        "demand_letter": "Demand Letter",
        "lease": "Lease Agreement",
        "service": "Service Agreement",
        "termination": "Termination Letter",
        "partnership": "Partnership Agreement",
    }

    def __init__(self, llm_client):
        self.llm = llm_client

    async def generate(
        self,
        scenario: str,
        documents: List[Dict] = None,
        doc_type: str = "legal_notice",
        parties: str = "Party A and Party B",
        jurisdiction: str = "India",
    ) -> str:
        """Generate a legal draft document."""
        context = ""
        if documents:
            context = "\n\n".join([d.get("text", "")[:500] for d in documents[:3]])

        prompt = f"""You are an expert legal draftsman practicing in {jurisdiction}.

Scenario: {scenario}
Document Type: {self.TEMPLATES.get(doc_type, doc_type)}
Parties: {parties}
Jurisdiction: {jurisdiction}
{f'Reference Documents Context: {context}' if context else ''}

Generate a complete, professional legal draft with:
1. Title and date
2. Parties section
3. Recitals / background
4. Main clauses (numbered)
5. Signatures block
6. Jurisdiction clause

Use formal legal language appropriate for Indian courts. Include relevant statutes where applicable.

DRAFT:"""

        try:
            draft = await self.llm.generate(prompt, temperature=0.2, max_tokens=3000)
            return draft
        except Exception as e:
            logger.error(f"Draft generation error: {e}")
            return f"Error generating draft: {str(e)}"

    async def summarize_document(self, text: str) -> Dict:
        """Summarize a legal document."""
        prompt = f"""Summarize this legal document in structured format.

Document:
{text[:3000]}

Provide:
1. Document Type
2. Parties Involved
3. Key Obligations (bullet points)
4. Important Dates/Deadlines
5. Termination Conditions
6. Governing Law
7. Risk Level (LOW/MEDIUM/HIGH)
8. Key Recommendations

Summary:"""
        try:
            summary = await self.llm.generate(prompt, temperature=0.1)
            return {"summary": summary, "success": True}
        except Exception as e:
            return {"summary": str(e), "success": False}
