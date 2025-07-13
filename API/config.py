"""
Configuration settings for the SPARQL API
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_title: str = "MES Ontology SPARQL API"
    api_version: str = "1.0.0"
    api_description: str = "Execute SPARQL queries against MES manufacturing ontology"
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    reload: bool = Field(default=False, env="API_RELOAD")
    
    # Thread Pool Configuration
    thread_pool_size: int = Field(default=4, env="THREAD_POOL_SIZE")
    query_timeout_seconds: int = Field(default=60, env="QUERY_TIMEOUT")  # Increased from 30s
    
    # Query Limits
    max_query_length: int = Field(default=10240, env="MAX_QUERY_LENGTH")  # 10KB
    max_result_rows: Optional[int] = Field(default=None, env="MAX_RESULT_ROWS")
    
    # Ontology Configuration
    ontology_path: Path = Field(
        default=Path(__file__).parent.parent / "Ontology" / "mes_ontology_populated.owl",
        env="ONTOLOGY_PATH"
    )
    ontology_iri: str = Field(
        default="http://mes-ontology.org/factory.owl",
        env="ONTOLOGY_IRI"
    )
    
    # CORS Configuration
    cors_enabled: bool = Field(default=True, env="CORS_ENABLED")
    cors_origins: list[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()