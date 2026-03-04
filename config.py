"""Configuration for Glamping Market Research AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COMPARABLES_DIR = DATA_DIR / "comparables"
REPORTS_DIR = DATA_DIR / "reports"
CACHE_DIR = DATA_DIR / "cache"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

# Ensure directories exist
for d in [DATA_DIR, COMPARABLES_DIR, REPORTS_DIR, CACHE_DIR, CHROMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _get(key: str, default: str = "") -> str:
    """Read env at runtime (supports UI-overridden keys)."""
    return os.getenv(key, default) or default


# Runtime getters for API keys and URLs (so UI can override via os.environ)
def get_browserbase_api_key() -> str:
    return _get("BROWSERBASE_API_KEY")


def get_browserbase_project_id() -> str:
    return _get("BROWSERBASE_PROJECT_ID")


def use_browserbase() -> bool:
    return bool(get_browserbase_api_key() and get_browserbase_project_id())


def get_ollama_base_url() -> str:
    return _get("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_model() -> str:
    return _get("OLLAMA_MODEL", "llama3.2")


def get_ollama_embedding_model() -> str:
    return _get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def get_openai_api_key() -> str:
    return _get("OPENAI_API_KEY")


def use_mock_scraping() -> bool:
    return _get("MOCK_SCRAPING", "").lower() in ("1", "true", "yes")



# Industry defaults
DEFAULT_OCCUPANCY_TOURISM = 0.625  # 55-70% midpoint
DEFAULT_OCCUPANCY_RURAL = 0.425  # 35-50% midpoint
CLEANING_COST_PER_TURN = 75
BOOKING_PLATFORM_FEE = 0.03  # 3%
PROPERTY_TAX_RATE = 0.01  # 1% of property value
INSURANCE_RATE = 0.002  # 0.2% of property value
MAINTENANCE_RATE = 0.02  # 2% of property value
MARKETING_RATE = 0.05  # 5% of revenue
