"""Logging configuration for agent decisions and research steps."""
import logging
import sys
from pathlib import Path

# Ensure data dir exists
try:
    from config import CACHE_DIR
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
LOG_FILE = Path(__file__).parent.parent / "data" / "research.log"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for agents, scrapers, and research steps."""
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )
    # Reduce noise from third-party libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def log_agent_decision(agent: str, action: str, details: dict) -> None:
    """Log agent decision for debugging."""
    logger = logging.getLogger("agents")
    logger.info("Agent=%s Action=%s Details=%s", agent, action, details)


def log_research_step(step: str, source: str, result_count: int) -> None:
    """Log research step (scraped source)."""
    logger = logging.getLogger("research")
    logger.info("Step=%s Source=%s Results=%d", step, source, result_count)
