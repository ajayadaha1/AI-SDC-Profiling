import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "AI SDC Profiling"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://aisdcprofiling:aisdcprofiling@localhost:5435/aisdcprofiling_db",
    )

    # CORS
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5175,https://failsafe.amd.com",
    )

    # AMD LLM Gateway
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "https://llm-api.amd.com/OpenAI")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))

    # Vision API (OnPrem)
    VISION_ENDPOINT: str = os.getenv("VISION_ENDPOINT", "https://llm-api.amd.com/OnPrem")
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "Meta-Llama-4-Maverick-17B")

    # RAG / Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "3072"))

    # Snowflake
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER", "")
    SNOWFLAKE_ROLE: str = os.getenv("SNOWFLAKE_ROLE", "PUBLIC")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE", "")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE", "")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA", "")
    SNOWFLAKE_PRIVATE_KEY_PATH: str = os.getenv(
        "SNOWFLAKE_PRIVATE_KEY_PATH", "/app/.snowflake/rsa_key.p8"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def snowflake_configured(self) -> bool:
        return bool(self.SNOWFLAKE_ACCOUNT and self.SNOWFLAKE_USER)

    @property
    def snowflake_key_available(self) -> bool:
        return os.path.exists(self.SNOWFLAKE_PRIVATE_KEY_PATH)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
