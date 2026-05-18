from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""

    pinecone_api_key: str = ""
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "legal-advisor"

    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    tavily_api_key: str = ""

    top_k: int = 10
    similarity_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    child_chunk_size: int = 200
    parent_chunk_size: int = 1000
    self_rag_threshold: float = 0.8
    mcts_iterations: int = 100
    mcts_exploration_constant: float = 1.414
    mcp_port: int = 8001
    allowed_origins: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
