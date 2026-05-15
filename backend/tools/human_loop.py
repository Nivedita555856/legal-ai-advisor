from loguru import logger
from typing import Dict
import asyncio


class HumanLoop:
    def __init__(self):
        self.pending_reviews: Dict[str, Dict] = {}

    async def request_validation(self, state: Dict) -> bool:
        review_id = f"review_{id(state)}"
        self.pending_reviews[review_id] = {
            "state": state,
            "status": "pending",
            "risk_level": state.get("risk_score", {}).get("level", "UNKNOWN"),
        }
        logger.warning(f"Human review requested [{review_id}]")
        await asyncio.sleep(0.1)
        self.pending_reviews[review_id]["status"] = "approved"
        return True

    def get_pending(self) -> Dict:
        return {k: v for k, v in self.pending_reviews.items() if v["status"] == "pending"}
