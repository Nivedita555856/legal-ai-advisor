from pinecone import Pinecone, ServerlessSpec
from loguru import logger
from typing import List, Dict
from config import settings

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
        logger.info("Loaded fastembed model: all-MiniLM-L6-v2 (ONNX, ~80MB)")
    return _embedder

def embed_text(text: str) -> List[float]:
    try:
        embeddings = list(get_embedder().embed([text[:512]]))
        return embeddings[0].tolist()
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return [0.0] * settings.embedding_dimension


class VectorStore:
    def __init__(self):
        self.pc = None
        self.index = None
        try:
            self.pc = Pinecone(api_key=settings.pinecone_api_key)
            self._ensure_index()
            self.index = self.pc.Index(settings.pinecone_index_name)
            logger.info("Pinecone index connected")
        except Exception as e:
            logger.warning(f"Pinecone init skipped: {e}")

    def _ensure_index(self):
        existing = [idx.name for idx in self.pc.list_indexes()]
        if settings.pinecone_index_name not in existing:
            self.pc.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info(f"Created Pinecone index: {settings.pinecone_index_name}")

    def _embed(self, text: str) -> List[float]:
        return embed_text(text)

    def upsert(self, vectors: List[Dict]):
        if not self.index:
            return
        try:
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                self.index.upsert(vectors=vectors[i:i + batch_size])
        except Exception as e:
            logger.error(f"Pinecone upsert error: {e}")

    def search(self, query: str, top_k: int = 10, filter: Dict = None) -> List[Dict]:
        if not self.index:
            return []
        try:
            embedding = self._embed(query)
            kwargs = {"vector": embedding, "top_k": top_k, "include_metadata": True}
            if filter:
                kwargs["filter"] = filter
            result = self.index.query(**kwargs)
            return [
                {
                    "id": m.id, "score": m.score,
                    "text": m.metadata.get("text", ""),
                    "document": m.metadata.get("document", ""),
                    "doc_id": m.metadata.get("doc_id", ""),
                    "chunk_index": m.metadata.get("chunk_index", 0),
                    "page": m.metadata.get("page", 0),
                }
                for m in result.matches
            ]
        except Exception as e:
            logger.error(f"Pinecone search error: {e}")
            return []

    def get_stats(self) -> Dict:
        if not self.index:
            return {}
        try:
            return self.index.describe_index_stats().to_dict()
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}

    def delete_all(self):
        if not self.index:
            return
        try:
            self.index.delete(delete_all=True)
        except Exception as e:
            logger.error(f"Clear error: {e}")

    def delete_by_doc_id(self, doc_id: str):
        if not self.index:
            return
        try:
            self.index.delete(filter={"doc_id": doc_id})
        except Exception as e:
            logger.error(f"Delete error: {e}")
