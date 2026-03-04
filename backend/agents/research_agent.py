"""ResearchAgent - scrapes comparable listings."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.models import ComparableListing
from backend.scrapers import (
    AirbnbScraper,
    HipcampScraper,
    GlampingHubScraper,
    GoogleMapsScraper,
    ZillowScraper,
    RedfinScraper,
)


def _get_mock_comparables(search_query: str) -> list[ComparableListing]:
    """Return sample comparables when scraping is disabled or fails."""
    scrapers = [
        AirbnbScraper(None, search_query),
        HipcampScraper(None, search_query),
        GlampingHubScraper(None, search_query),
    ]
    all_listings = []
    for scraper in scrapers:
        try:
            listings = scraper.scrape(search_query)
            all_listings.extend(listings)
        except Exception:
            pass
    return all_listings[:15]


def research_agent(state: AnalysisState) -> AnalysisState:
    """Scrape comparables from multiple sources."""
    prop = state["property_input"]
    search_query = prop.property_address

    use_mock = os.getenv("MOCK_SCRAPING", "").lower() in ("1", "true", "yes")

    if use_mock:
        unique = _get_mock_comparables(search_query)
        return {**state, "comparables": unique}

    all_listings = []
    try:
        from backend.browser.browser_manager import get_browser_manager
        manager = get_browser_manager()
        page, mgr = manager.get_page()
        try:
            scrapers = [
                AirbnbScraper(page, search_query),
                HipcampScraper(page, search_query),
                GlampingHubScraper(page, search_query),
                GoogleMapsScraper(page, search_query),
                ZillowScraper(page, search_query),
                RedfinScraper(page, search_query),
            ]
            for scraper in scrapers:
                try:
                    listings = scraper.scrape(search_query)
                    all_listings.extend(listings)
                except Exception:
                    pass
        finally:
            mgr.cleanup()
    except Exception:
        unique = _get_mock_comparables(search_query)
        return {**state, "comparables": unique}

    # Dedupe by name
    seen = set()
    unique = []
    for L in all_listings:
        key = (L.name[:50], L.source)
        if key not in seen:
            seen.add(key)
            unique.append(L)

    if not unique:
        unique = _get_mock_comparables(search_query)

    return {**state, "comparables": unique}
