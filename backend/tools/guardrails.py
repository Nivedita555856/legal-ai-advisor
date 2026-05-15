from loguru import logger
from typing import Dict, Optional


class Guardrails:
    """Input/output safety guardrails for legal AI."""

    BLOCKED_PATTERNS = [
        "provide false legal advice",
        "fabricate case law",
        "create fraudulent",
        "help evade",
        "launder",
    ]

    MAX_INPUT_LENGTH = 50_000  # characters

    def validate_input(self, query: str) -> Dict:
        """Validate user query."""
        query_lower = query.lower()

        if len(query) > self.MAX_INPUT_LENGTH:
            return {
                "valid": False,
                "reason": f"Query exceeds maximum length ({self.MAX_INPUT_LENGTH} chars).",
            }

        for pattern in self.BLOCKED_PATTERNS:
            if pattern in query_lower:
                return {
                    "valid": False,
                    "reason": f"Query contains disallowed content: '{pattern}'.",
                }

        return {"valid": True, "reason": None}

    def validate_output(self, answer: str) -> Dict:
        """Ensure output contains appropriate disclaimers."""
        has_disclaimer = any(
            phrase in answer.lower()
            for phrase in [
                "this is not legal advice",
                "consult a lawyer",
                "seek professional",
                "disclaimer",
            ]
        )
        if not has_disclaimer:
            answer = (
                answer
                + "\n\nNote: This analysis is for informational purposes only and does not constitute legal advice. Please consult a qualified lawyer for specific legal guidance."
            )
        return {"answer": answer, "disclaimer_added": not has_disclaimer}
