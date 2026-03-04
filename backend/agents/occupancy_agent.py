"""OccupancyAgent - estimates occupancy rate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.occupancy_model import estimate_occupancy


def occupancy_agent(state: AnalysisState) -> AnalysisState:
    """Estimate occupancy rate from market signals."""
    comparables = state.get("comparables", [])
    total_reviews = sum(c.reviews or 0 for c in comparables)

    # Assume tourism area if we have many comparables with reviews
    is_tourism = total_reviews > 100 or len(comparables) >= 3
    saturation = 0.98 if len(comparables) > 10 else 1.0

    occ = estimate_occupancy(
        comparables,
        is_tourism_area=is_tourism,
        total_reviews=total_reviews,
        market_saturation_factor=saturation,
    )
    return {**state, "occupancy_rate": occ}
