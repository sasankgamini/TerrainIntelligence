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
CHROMA_DIR = DATA_DIR / "chroma_db"

# Ensure directories exist
for d in [DATA_DIR, COMPARABLES_DIR, REPORTS_DIR, CACHE_DIR, CHROMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Browser
BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY")
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")
USE_BROWSERBASE = bool(BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID)

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# Industry defaults
DEFAULT_OCCUPANCY_TOURISM = 0.625  # 55-70% midpoint
DEFAULT_OCCUPANCY_RURAL = 0.425  # 35-50% midpoint
CLEANING_COST_PER_TURN = 75
BOOKING_PLATFORM_FEE = 0.03  # 3%
PROPERTY_TAX_RATE = 0.01  # 1% of property value
INSURANCE_RATE = 0.002  # 0.2% of property value
MAINTENANCE_RATE = 0.02  # 2% of property value
MARKETING_RATE = 0.05  # 5% of revenue
