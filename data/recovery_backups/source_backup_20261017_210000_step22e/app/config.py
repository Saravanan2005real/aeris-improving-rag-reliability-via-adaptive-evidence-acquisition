from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:latest"
    embedding_model: str = "nomic-embed-text:latest"
    ollama_timeout: float = 60.0
    ollama_connect_timeout: float = 10.0
    max_anomaly_latency_seconds: float = 300.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
