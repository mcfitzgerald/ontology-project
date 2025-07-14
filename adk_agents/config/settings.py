"""
Configuration settings and path management for ADK Manufacturing Analytics Agents.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for accessing ontology project files
ADK_AGENTS_DIR = Path(__file__).parent.parent
PROJECT_ROOT = ADK_AGENTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv(ADK_AGENTS_DIR / '.env')

# LLM Configuration
GOOGLE_GENAI_USE_VERTEXAI = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE').upper() == 'TRUE'
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', '')
GOOGLE_CLOUD_LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# SPARQL Configuration
SPARQL_ENDPOINT = os.getenv('SPARQL_ENDPOINT', 'http://localhost:8000/sparql/query')
SPARQL_TIMEOUT = int(os.getenv('SPARQL_TIMEOUT', '30000'))

# Analysis Configuration
DEFAULT_OEE_BENCHMARK = float(os.getenv('DEFAULT_OEE_BENCHMARK', '85.0'))
DEFAULT_ANALYSIS_WINDOW_DAYS = int(os.getenv('DEFAULT_ANALYSIS_WINDOW_DAYS', '14'))
ONTOLOGY_NAMESPACE = os.getenv('ONTOLOGY_NAMESPACE', 'http://example.com/mes#')

# Resource Paths
ONTOLOGY_DIR = PROJECT_ROOT / "Ontology"
CONTEXT_DIR = PROJECT_ROOT / "Context"
SPARQL_EXAMPLES_DIR = PROJECT_ROOT / "SPARQL_Examples"
DATA_DIR = PROJECT_ROOT / "Data"

# Specific Files
MINDMAP_FILE = CONTEXT_DIR / "mes_ontology_mindmap.ttl"
POPULATED_ONTOLOGY = ONTOLOGY_DIR / "mes_ontology_populated.owl"
MES_DATA_CSV = DATA_DIR / "mes_data_with_kpis.csv"

# SPARQL Reference Guides
OWLREADY2_SPARQL_GUIDE = SPARQL_EXAMPLES_DIR / "owlready2_sparql_master_reference.md"
LLM_ANALYSIS_GUIDE = SPARQL_EXAMPLES_DIR / "llm_driven_oee_analysis_guide.md"
LLM_SPARQL_GUIDE = SPARQL_EXAMPLES_DIR / "owlready2_sparql_llm_guide.md"

# Model Configuration
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0.1  # Low temperature for consistent analysis

# Validation
def validate_config():
    """Validate configuration settings."""
    if GOOGLE_GENAI_USE_VERTEXAI and not GOOGLE_CLOUD_PROJECT:
        raise ValueError("GOOGLE_CLOUD_PROJECT must be set when using Vertex AI")
    
    if not GOOGLE_GENAI_USE_VERTEXAI and not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY must be set when not using Vertex AI")
    
    if not MINDMAP_FILE.exists():
        print(f"Warning: Ontology mindmap not found at {MINDMAP_FILE}")
    
    return True

# Run validation on import
try:
    validate_config()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file settings")