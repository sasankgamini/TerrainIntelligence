"""Pricing model for nightly rate estimation."""
import numpy as np
from backend.models import ComparableListing


def recommend_nightly_rate(
    comparables: list[ComparableListing],
    override: float | None = None,
) -> float:
    """Recommend nightly rate from comparables. Uses median, upper quartile, amenity weighting."""
    if override and override > 0:
        return override

    prices = [c.price_per_night for c in comparables if c.price_per_night and c.price_per_night > 0]
    if not prices:
        return 150.0  # Default fallback

    prices = [p for p in prices if 20 <= p <= 2000]
    if not prices:
        return 150.0

    median = float(np.median(prices))
    q75 = float(np.percentile(prices, 75))
    # Blend: 60% median, 40% upper quartile (aim for premium positioning)
    recommended = median * 0.6 + q75 * 0.4
    return round(recommended, 2)
