"""BrowserAgent - controls Playwright/Browserbase for multi-step browsing."""
import sys
import time
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.models import ComparableListing

logger = logging.getLogger(__name__)

# Scraper mapping for plan actions
SCRAPER_MAP = {
    "airbnb": "AirbnbScraper",
    "hipcamp": "HipcampScraper",
    "glampinghub": "GlampingHubScraper",
    "google_maps": "GoogleMapsScraper",
    "zillow": "ZillowScraper",
    "redfin": "RedfinScraper",
}


def search_google(page, query: str) -> str:
    """Search Google and return page content."""
    if not page:
        return ""
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        page.goto(url, wait_until="networkidle", timeout=15000)
        time.sleep(2)
        return page.content()
    except Exception as e:
        logger.warning("search_google failed: %s", e)
        return ""


def visit_url(page, url: str) -> str:
    """Visit URL and return page content."""
    if not page:
        return ""
    try:
        page.goto(url, wait_until="networkidle", timeout=15000)
        time.sleep(2)
        return page.content()
    except Exception as e:
        logger.warning("visit_url failed: %s", e)
        return ""


def _get_scraper_instance(scraper_name: str, page, search_query: str):
    """Get scraper instance by name."""
    from backend.scrapers import (
        AirbnbScraper,
        HipcampScraper,
        GlampingHubScraper,
        GoogleMapsScraper,
        ZillowScraper,
        RedfinScraper,
    )
    scrapers = {
        "airbnb": AirbnbScraper,
        "hipcamp": HipcampScraper,
        "glampinghub": GlampingHubScraper,
        "google_maps": GoogleMapsScraper,
        "zillow": ZillowScraper,
        "redfin": RedfinScraper,
    }
    cls = scrapers.get(scraper_name)
    if cls:
        return cls(page, search_query)
    return None


def browser_agent(state: AnalysisState) -> AnalysisState:
    """
    Execute browsing tasks from the research plan.
    Runs scrapers for each planned step, supports multi-step browsing.
    """
    from config import use_mock_scraping

    prop = state.get("property_input")
    plan = state.get("research_plan")
    existing_comparables = state.get("comparables", [])
    research_log = state.get("research_log", [])

    search_query = prop.property_address if prop else ""

    if use_mock_scraping():
        # Use mock data path
        from backend.agents.research_agent import _get_mock_comparables
        mock_listings = _get_mock_comparables(search_query)
        research_log.append({
            "agent": "browser",
            "action": "mock_scraping",
            "listings_found": len(mock_listings),
            "message": "Using mock data (MOCK_SCRAPING=1)",
        })
        return {
            **state,
            "comparables": mock_listings,
            "research_log": research_log,
        }

    all_listings = list(existing_comparables)
    steps_to_run = plan.steps if plan else []

    # Filter to scrapers we support (skip "tourism" for now - handled separately)
    scrapers_to_run = [s for s in steps_to_run if s.get("scraper") in SCRAPER_MAP and s.get("scraper") != "tourism"]

    try:
        from backend.browser.browser_manager import get_browser_manager
        manager = get_browser_manager()
        page, mgr = manager.get_page()
        try:
            for step in scrapers_to_run:
                scraper_name = step.get("scraper")
                scraper = _get_scraper_instance(scraper_name, page, search_query)
                if scraper:
                    try:
                        listings = scraper.scrape(search_query)
                        all_listings.extend(listings)
                        research_log.append({
                            "agent": "browser",
                            "action": step.get("action", scraper_name),
                            "scraper": scraper_name,
                            "listings_found": len(listings),
                            "source_url": getattr(listings[0], "source_url", "") if listings else "",
                        })
                        logger.info("Browser: %s found %d listings", scraper_name, len(listings))
                    except Exception as e:
                        research_log.append({
                            "agent": "browser",
                            "action": step.get("action"),
                            "scraper": scraper_name,
                            "error": str(e),
                        })
                        logger.warning("Browser: %s failed: %s", scraper_name, e)
        finally:
            mgr.cleanup()
    except Exception as e:
        logger.error("Browser agent failed: %s", e)
        research_log.append({"agent": "browser", "action": "init", "error": str(e)})
        # Fallback to mock if browser fails
        from backend.agents.research_agent import _get_mock_comparables
        all_listings = _get_mock_comparables(search_query)

    # Dedupe by (name, source)
    seen = set()
    unique = []
    for L in all_listings:
        key = (L.name[:50], L.source)
        if key not in seen:
            seen.add(key)
            unique.append(L)

    research_log.append({
        "agent": "browser",
        "action": "extract_complete",
        "total_listings": len(unique),
        "message": f"Extracted {len(unique)} unique listings",
    })

    return {
        **state,
        "comparables": unique,
        "research_log": research_log,
    }
