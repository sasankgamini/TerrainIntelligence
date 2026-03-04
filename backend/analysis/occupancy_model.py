"""Occupancy estimation model."""
from config import DEFAULT_OCCUPANCY_TOURISM, DEFAULT_OCCUPANCY_RURAL


def estimate_occupancy(
    comparables: list,
    is_tourism_area: bool = True,
    total_reviews: int = 0,
    market_saturation_factor: float = 1.0,
) -> float:
    """
    Estimate occupancy rate.
    Tourism: 55-70%, Rural: 35-50%.
    Adjust for review activity and market saturation.
    """
    base = DEFAULT_OCCUPANCY_TOURISM if is_tourism_area else DEFAULT_OCCUPANCY_RURAL

    # Review activity: more reviews = more demand
    if total_reviews > 500:
        adj = 1.05
    elif total_reviews > 200:
        adj = 1.02
    elif total_reviews < 50:
        adj = 0.95
    else:
        adj = 1.0

    # Market saturation: more competition = lower occupancy
    occ = base * adj * market_saturation_factor
    return round(max(0.25, min(0.75, occ)), 4)


def seasonal_adjustment(monthly_occupancy: list[float]) -> list[float]:
    """Apply seasonal demand pattern (US camping: peak summer)."""
    # Typical US camping: higher in summer, lower in winter
    factors = [0.6, 0.55, 0.7, 0.85, 1.0, 1.1, 1.15, 1.1, 0.95, 0.8, 0.65, 0.6]  # Jan-Dec
    base_avg = sum(monthly_occupancy) / 12 if monthly_occupancy else 0.5
    return [base_avg * f for f in factors]
