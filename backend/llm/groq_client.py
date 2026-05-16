from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict
import json

from config import settings

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


class GroqClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._client = None
        self._setup()

    def _setup(self):
        if self.provider == "claude":
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.model = settings.claude_model
                logger.info(f"LLM: Claude ({self.model})")
            except ImportError:
                self.provider = "groq"
                self._setup_groq()
        else:
            self._setup_groq()

    def _setup_groq(self):
        from groq import Groq
        self._client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        logger.info(f"LLM: Groq ({self.model})")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 1024) -> str:
        try:
            if self.provider == "claude":
                return await self._generate_claude(prompt, temperature, max_tokens)
            return await self._generate_groq(prompt, temperature, max_tokens)
        except Exception as e:
            logger.error(f"LLM generate error ({self.provider}): {e}")
            raise

    async def _generate_groq(self, prompt: str, temperature: float, max_tokens: int) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an Indian legal document analyst. Write in plain English without markdown formatting."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _generate_claude(self, prompt: str, temperature: float, max_tokens: int) -> str:
        import asyncio
        def _call():
            return self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an Indian legal document analyst. Write in plain English without markdown formatting, bold text, or emojis.",
                messages=[{"role": "user", "content": prompt}],
            )
        response = await asyncio.to_thread(_call)
        return response.content[0].text if response.content else ""

    async def embed(self, text: str) -> List[float]:
        try:
            vec = get_embedder().encode(text[:512], normalize_embeddings=True)
            return vec.tolist()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * settings.embedding_dimension

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            vecs = get_embedder().encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            return [[0.0] * settings.embedding_dimension for _ in texts]

    async def assess_risks(self, query: str, chunks: List[Dict]) -> Dict:
        context = "\n".join([c.get("text", "")[:200] for c in chunks[:2]])
        prompt = f"""Rate the legal risk for this query in JSON only.
Query: {query[:200]}
Context: {context}
Return exactly: {{"score": 50, "level": "LOW", "factors": [], "recommendation": "Review recommended."}}"""
        try:
            raw = await self.generate(prompt, temperature=0, max_tokens=256)
            s = raw.find("{"); e = raw.rfind("}") + 1
            if s >= 0 and e > s:
                return json.loads(raw[s:e])
        except Exception as ex:
            logger.warning(f"Risk parse error: {ex}")
        return {"score": 50, "level": "MEDIUM", "factors": [], "recommendation": "Manual review recommended."}

    async def detect_contradictions_batch(self, chunks: List[Dict]) -> List[Dict]:
        texts = [c.get("text", "")[:200] for c in chunks[:2]]
        if len(texts) < 2:
            return []
        prompt = f"""Do these two legal clauses contradict each other? Reply in JSON only.
Clause 1: {texts[0]}
Clause 2: {texts[1]}
Return: [{{"clause_a": 1, "clause_b": 2, "has_contradiction": false, "severity": "LOW", "explanation": ""}}]"""
        try:
            raw = await self.generate(prompt, temperature=0, max_tokens=256)
            s = raw.find("["); e = raw.rfind("]") + 1
            if s >= 0 and e > s:
                return json.loads(raw[s:e])
        except Exception as ex:
            logger.warning(f"Contradiction error: {ex}")
        return []
