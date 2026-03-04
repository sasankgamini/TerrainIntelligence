"""PropertyScoutAgent - finds land with high ROI potential."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scrapers import LandWatchScraper, ZillowScraper, RedfinScraper
from backend.models import ScoutInput


def _get_mock_scout_results(scout_input: ScoutInput) -> list[dict]:
    """Return sample scout results when scraping is disabled or fails."""
    listings = LandWatchScraper(None, "")._get_mock_results(f"{scout_input.county} {scout_input.state}")
    results = []
    for L in listings:
        raw = getattr(L, "raw_data", {}) or {}
        acreage = raw.get("acreage", scout_input.min_acreage)
        list_price = raw.get("list_price", (scout_input.budget_min + scout_input.budget_max) / 2)
        est_units = max(1, int(acreage / 2.5))
        est_rev = est_units * 120 * 365 * 0.5
        est_noi = est_rev * 0.6
        est_roi = (est_noi / list_price * 100) if list_price > 0 else 0
        results.append({
            "name": L.name,
            "location": L.location,
            "acreage": acreage,
            "list_price": list_price,
            "source": L.source,
            "source_url": L.source_url,
            "est_units": est_units,
            "est_revenue": est_rev,
            "est_roi": round(est_roi, 2),
        })
    results.sort(key=lambda x: x["est_roi"], reverse=True)
    return results


def scout_properties(scout_input: ScoutInput) -> list[dict]:
    """
    Scrape land listings and rank by estimated ROI.
    Returns list of dicts with property info and estimated metrics.
    """
    from config import use_mock_scraping

    use_mock = use_mock_scraping()
    if use_mock:
        return _get_mock_scout_results(scout_input)

    search_query = f"{scout_input.county} {scout_input.state}"
    all_listings = []

    try:
        from backend.browser.browser_manager import get_browser_manager
        manager = get_browser_manager()
        page, mgr = manager.get_page()
        try:
            scrapers = [
                LandWatchScraper(page, search_query),
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
        return _get_mock_scout_results(scout_input)

    # Convert to scout results with ROI estimates
    results = []
    for L in all_listings:
        raw = getattr(L, "raw_data", {}) or {}
        acreage = raw.get("acreage") or scout_input.min_acreage
        list_price = raw.get("list_price") or (scout_input.budget_min + scout_input.budget_max) / 2

        if list_price < scout_input.budget_min or list_price > scout_input.budget_max:
            continue
        if acreage < scout_input.min_acreage:
            continue

        # Estimate capacity: ~2 units per 5 acres for glamping
        est_units = max(1, int(acreage / 2.5))
        est_nightly = 120
        est_occ = 0.5
        est_rev = est_units * est_nightly * 365 * est_occ
        est_exp = est_rev * 0.4  # Rough
        est_noi = est_rev - est_exp
        est_roi = (est_noi / list_price * 100) if list_price > 0 else 0

        results.append({
            "name": L.name,
            "location": L.location,
            "acreage": acreage,
            "list_price": list_price,
            "source": L.source,
            "source_url": L.source_url,
            "est_units": est_units,
            "est_revenue": est_rev,
            "est_roi": round(est_roi, 2),
        })

    # Rank by ROI
    results.sort(key=lambda x: x["est_roi"], reverse=True)
    return results[:25]
