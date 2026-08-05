from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "IdeaForge"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ideaforge"

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # ── OpenAI — primary LLM (orchestration, complex reasoning) ──────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Google Gemini — secondary LLM (generation, evaluation) ───────────────
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # ── Groq — fast inference (scoring, quick classification) ─────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ── RAG — embeddings + pgvector ──────────────────────────────────────────
    openai_embedding_model: str = "text-embedding-3-small"
    openai_vision_model: str = "gpt-4o"   # used when PDF text extraction fails
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 80
    rag_top_k: int = 5

    # ── CORS — comma-separated allowed origins ────────────────────────────────
    # Example: ALLOWED_ORIGINS=https://my-app.vercel.app,https://www.myapp.com
    allowed_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"

    # ── LangSmith — optional workflow tracing ─────────────────────────────────
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
