"""PropertyScoutAgent - finds land with high ROI potential, runs capacity + financial model."""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scrapers import LandWatchScraper, ZillowScraper, RedfinScraper
from backend.models import ScoutInput, PropertyInput
from backend.analysis.capacity_estimation import estimate_capacity
from backend.analysis.financial_model import (
    annual_revenue,
    estimate_expenses,
    noi,
    roi,
    npv,
    irr,
    payback_period,
    financial_scenarios,
)

logger = logging.getLogger(__name__)


def _compute_investment_score(
    est_roi: float,
    capacity_units: int,
    permitting_risk: str,
) -> float:
    """investment_score = ROI weight + demand weight + competition weight + tourism weight."""
    roi_weight = min(1.0, est_roi / 15) * 0.35
    capacity_weight = min(1.0, capacity_units / 15) * 0.25
    risk_weight = 0.25 if permitting_risk == "low" else (0.15 if permitting_risk == "moderate" else 0.05)
    return round((roi_weight + capacity_weight + risk_weight + 0.2) * 100, 1)


def _get_mock_scout_results(scout_input: ScoutInput) -> list[dict]:
    """Return sample scout results when scraping is disabled or fails."""
    listings = LandWatchScraper(None, "")._get_mock_results(f"{scout_input.county} {scout_input.state}")
    results = []
    for L in listings:
        raw = getattr(L, "raw_data", {}) or {}
        acreage = raw.get("acreage", scout_input.min_acreage)
        list_price = raw.get("list_price", (scout_input.budget_min + scout_input.budget_max) / 2)
        capacity = estimate_capacity(acreage)
        est_units = capacity.total_units or max(1, int(acreage / 2.5))
        est_rev = est_units * 120 * 365 * 0.5
        est_noi = est_rev * 0.6
        est_roi = (est_noi / list_price * 100) if list_price > 0 else 0
        investment_score = _compute_investment_score(est_roi, est_units, capacity.permitting_risk)
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
            "est_npv": 0,
            "est_irr": 0,
            "investment_score": investment_score,
            "capacity_max_cabins": capacity.max_cabins,
            "capacity_max_glamping": capacity.max_glamping,
            "permitting_risk": capacity.permitting_risk,
        })
    results.sort(key=lambda x: x["investment_score"], reverse=True)
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

    # Convert to scout results with full capacity + financial model
    results = []
    for L in all_listings:
        raw = getattr(L, "raw_data", {}) or {}
        acreage = raw.get("acreage") or scout_input.min_acreage
        list_price = raw.get("list_price") or (scout_input.budget_min + scout_input.budget_max) / 2

        if list_price < scout_input.budget_min or list_price > scout_input.budget_max:
            continue
        if acreage < scout_input.min_acreage:
            continue

        # Estimate development capacity from acreage
        capacity = estimate_capacity(acreage)
        est_units = capacity.total_units or max(1, int(acreage / 2.5))

        # Run financial model: assume glamping-heavy mix
        est_nightly = 120
        est_occ = 0.5
        est_rev = annual_revenue(est_units, est_nightly, est_occ)
        property_value = list_price * 1.2  # Assume some development cost
        expenses = estimate_expenses(est_rev, est_units, est_occ, property_value)
        est_noi = noi(est_rev, expenses)
        investment = list_price + (est_units * 15000)  # Land + development
        est_roi = roi(investment, est_noi)

        # Financial scenarios
        scenarios = financial_scenarios(est_units, est_nightly, est_occ, expenses, investment)
        base_npv = scenarios.get("base_case", {}).get("npv", 0)
        base_irr = scenarios.get("base_case", {}).get("irr", 0)

        investment_score = _compute_investment_score(est_roi, est_units, capacity.permitting_risk)

        results.append({
            "name": L.name,
            "location": L.location,
            "acreage": acreage,
            "list_price": list_price,
            "source": L.source,
            "source_url": L.source_url,
            "est_units": est_units,
            "est_revenue": round(est_rev, 2),
            "est_roi": round(est_roi, 2),
            "est_npv": base_npv,
            "est_irr": base_irr,
            "investment_score": investment_score,
            "capacity_max_cabins": capacity.max_cabins,
            "capacity_max_glamping": capacity.max_glamping,
            "permitting_risk": capacity.permitting_risk,
        })

    # Rank by investment_score (ROI + demand + capacity + risk)
    results.sort(key=lambda x: x["investment_score"], reverse=True)
    return results[:25]
