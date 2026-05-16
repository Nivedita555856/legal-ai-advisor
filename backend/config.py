from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "legal-advisor"

    # LLM Provider: "groq" or "claude"
    llm_provider: str = "groq"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Anthropic Claude
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # Embedding model (local)
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # OpenAI (embeddings fallback)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Neo4j
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # Tavily
    tavily_api_key: str = ""

    # RAG Parameters
    top_k: int = 10
    similarity_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Parent-Child RAG
    child_chunk_size: int = 200
    parent_chunk_size: int = 1000

    # Self RAG
    self_rag_threshold: float = 0.8

    # MCTS
    mcts_iterations: int = 100
    mcts_exploration_constant: float = 1.414

    # MCP Server
    mcp_port: int = 8001

    # CORS
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
