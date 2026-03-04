"""VerifierAgent - validates research results and computes confidence scores."""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.models import ComparableListing, VerifiedDataset

logger = logging.getLogger(__name__)


def _normalize_price(price: float) -> float:
    """Normalize price to reasonable range for comparison."""
    if not price or price <= 0:
        return 0
    return min(max(price, 20), 2000)


def _cross_check_pricing(comparables: list[ComparableListing]) -> float:
    """
    Cross-check pricing across sources. Higher consistency = higher confidence.
    Returns 0-1 score.
    """
    if not comparables:
        return 0.0

    prices = [c.price_per_night for c in comparables if c.price_per_night and c.price_per_night > 0]
    if len(prices) < 2:
        return 0.6  # Single source - moderate confidence

    import numpy as np
    median = float(np.median(prices))
    std = float(np.std(prices)) if len(prices) > 1 else 0
    cv = std / median if median > 0 else 1  # Coefficient of variation
    # Lower CV = more consistent = higher confidence
    confidence = max(0.3, min(1.0, 1.0 - cv * 0.5))
    return round(confidence, 2)


def _count_unique_sources(comparables: list[ComparableListing]) -> int:
    """Count unique data sources."""
    return len(set(c.source for c in comparables if c.source))


def _remove_duplicates(comparables: list[ComparableListing]) -> list[ComparableListing]:
    """Remove duplicate listings by name+source, prefer higher-rated."""
    seen = {}
    for c in comparables:
        key = (c.name[:60].lower(), c.source)
        if key not in seen or (c.rating or 0) > (seen[key].rating or 0):
            seen[key] = c
    return list(seen.values())


def verifier_agent(state: AnalysisState) -> AnalysisState:
    """
    Validate research results.
    - Remove duplicate listings
    - Verify pricing accuracy
    - Cross-check data across sources
    - Compute confidence_score and source_count
    """
    comparables = state.get("comparables", [])
    research_log = state.get("research_log", [])

    # Remove duplicates
    deduped = _remove_duplicates(comparables)

    # Compute confidence from pricing consistency
    pricing_confidence = _cross_check_pricing(deduped)

    # Factor in source diversity
    source_count = _count_unique_sources(deduped)
    source_factor = min(1.0, 0.5 + source_count * 0.1)  # 1 source=0.6, 3+=0.8+

    # Factor in data completeness (listings with price + rating)
    complete = sum(1 for c in deduped if c.price_per_night and c.price_per_night > 0 and c.rating)
    total_with_price = sum(1 for c in deduped if c.price_per_night and c.price_per_night > 0)
    completeness = (complete / len(deduped)) if deduped else 0
    completeness_factor = 0.5 + completeness * 0.5

    confidence_score = (pricing_confidence * 0.5 + source_factor * 0.3 + completeness_factor * 0.2)
    confidence_score = round(min(1.0, max(0.2, confidence_score)), 2)

    verified = VerifiedDataset(
        comparables=deduped,
        confidence_score=confidence_score,
        source_count=source_count,
    )

    research_log.append({
        "agent": "verifier",
        "action": "verify",
        "input_count": len(comparables),
        "output_count": len(deduped),
        "confidence_score": confidence_score,
        "source_count": source_count,
        "message": f"Verified {len(deduped)} listings, confidence={confidence_score:.2f}",
    })

    logger.info("Verifier: %d listings, confidence=%.2f, sources=%d",
                len(deduped), confidence_score, source_count)

    return {
        **state,
        "comparables": deduped,
        "verified_dataset": verified,
        "research_log": research_log,
    }
