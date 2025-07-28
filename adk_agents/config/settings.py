"""Configuration settings for ADK Agents system."""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
CACHE_DIR = PROJECT_ROOT / "cache"
CONTEXT_DIR = PROJECT_ROOT / "context"

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
CONTEXT_DIR.mkdir(exist_ok=True)

# LLM Configuration
USE_VERTEX_AI = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "adk-exploration")
LOCATION = os.getenv("VERTEX_LOCATION", "us-east1")

# Model Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))

# SPARQL Configuration
SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://localhost:8000/sparql/query")
SPARQL_TIMEOUT = int(os.getenv("SPARQL_TIMEOUT", "30"))
SPARQL_MAX_RESULTS = int(os.getenv("SPARQL_MAX_RESULTS", "1000"))

# Analysis Configuration
OEE_BENCHMARK = float(os.getenv("OEE_BENCHMARK", "85.0"))
ONTOLOGY_NAMESPACE = os.getenv("ONTOLOGY_NAMESPACE", "http://www.semanticweb.org/michael/ontologies/2024/mes-ontology#")

# Resource Paths
ONTOLOGY_FILE = os.getenv("ONTOLOGY_FILE", "Ontology/mes_ontology_populated.owl")
SPARQL_EXAMPLES_DIR = os.getenv("SPARQL_EXAMPLES_DIR", "sparql_examples")
DATA_DIR = os.getenv("DATA_DIR", "data")

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "48"))  # 80% of Vertex AI limit
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Cache Configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))  # entries

# Vertex AI specific settings
if USE_VERTEX_AI:
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration based on authentication method."""
    config = {
        "model": DEFAULT_MODEL,
        "temperature": MODEL_TEMPERATURE,
        "max_output_tokens": MAX_OUTPUT_TOKENS
    }
    
    if USE_VERTEX_AI:
        config.update({
            "project": PROJECT_ID,
            "location": LOCATION
        })
    else:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set when not using Vertex AI")
        config["api_key"] = GOOGLE_API_KEY
    
    return config

def get_sparql_config() -> Dict[str, Any]:
    """Get SPARQL configuration."""
    return {
        "endpoint": SPARQL_ENDPOINT,
        "timeout": SPARQL_TIMEOUT,
        "max_results": SPARQL_MAX_RESULTS,
        "namespace": ONTOLOGY_NAMESPACE
    }

