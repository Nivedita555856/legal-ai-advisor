from tavily import TavilyClient
from loguru import logger
from config import settings


class WebSearch:
    def __init__(self):
        try:
            self.client = TavilyClient(api_key=settings.tavily_api_key)
            logger.info("Tavily connected")
        except Exception as e:
            logger.warning(f"Tavily init skipped: {e}")
            self.client = None

    async def search(self, query: str, max_results: int = 5) -> str:
        if not self.client:
            return "Web search not available."
        try:
            results = self.client.search(
                query=f"Indian law legal {query}",
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
            )
            if results.get("answer"):
                return results["answer"]
            texts = [r.get("content", "") for r in results.get("results", [])[:3]]
            return "\n\n".join(texts)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Web search failed: {str(e)}"
