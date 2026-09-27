

"""Core configuration loaded from environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "production"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = int(os.getenv("PORT", 8000))
    log_level: str = "INFO"

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Hybrid Search Weights
    hybrid_weight_lexical: float = 0.35
    hybrid_weight_semantic: float = 0.55
    hybrid_weight_metadata: float = 0.10

    # Paths (relative to backend/)
    vector_index_path: str = "vector_store/index.faiss"
    standards_data_path: str = "data/standards/standards.json"
    relationships_data_path: str = "data/relationships/relationships.json"
    qco_data_path: str = "data/compliance/qco.json"

    # Limits
    max_file_size_mb: int = 20
    ocr_min_text_length: int = 50

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
