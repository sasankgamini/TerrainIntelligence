"""Tourism demand signals for occupancy adjustment."""
from backend.models import ComparableListing, TourismDemandSignals


def gather_tourism_signals(
    comparables: list[ComparableListing],
    scraped_sources: list[str] | None = None,
) -> TourismDemandSignals:
    """
    Gather tourism demand signals from comparables and optional scraped data.
    Signals: review counts, search popularity, number of attractions nearby.
    """
    total_reviews = sum(c.reviews or 0 for c in comparables)
    avg_rating = 0
    rated = [c for c in comparables if c.rating and c.rating > 0]
    if rated:
        avg_rating = sum(c.rating for c in rated) / len(rated)

    # Estimate attractions from number of unique sources/listings (proxy for market activity)
    unique_sources = len(set(c.source for c in comparables))
    # More listings + more sources = more tourism activity
    attractions_proxy = min(10, len(comparables) // 2 + unique_sources)

    # Search popularity: 0-1 based on review volume and listing count
    review_score = min(1.0, total_reviews / 1000) if total_reviews else 0.3
    listing_score = min(1.0, len(comparables) / 20)
    search_popularity = (review_score * 0.6 + listing_score * 0.4)

    return TourismDemandSignals(
        review_counts=total_reviews,
        attractions_nearby=attractions_proxy,
        search_popularity_score=round(search_popularity, 2),
        sources=scraped_sources or list(set(c.source for c in comparables)),
    )


def adjust_occupancy_for_tourism(
    base_occupancy: float,
    signals: TourismDemandSignals,
) -> float:
    """
    Adjust occupancy estimate based on tourism demand signals.
    Higher review counts, more attractions = higher occupancy.
    """
    adj = 1.0
    if signals.review_counts > 500:
        adj += 0.05
    elif signals.review_counts > 200:
        adj += 0.02
    elif signals.review_counts < 50:
        adj -= 0.05

    if signals.attractions_nearby >= 5:
        adj += 0.03
    elif signals.attractions_nearby >= 3:
        adj += 0.01

    adj += (signals.search_popularity_score - 0.5) * 0.1  # Center at 0.5

    return round(max(0.25, min(0.75, base_occupancy * adj)), 4)
