"""OccupancyAgent - estimates occupancy rate with tourism demand signals."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.occupancy_model import estimate_occupancy
from backend.analysis.tourism_demand import gather_tourism_signals, adjust_occupancy_for_tourism
from backend.analysis.financial_model import seasonal_occupancy_curve


def occupancy_agent(state: AnalysisState) -> AnalysisState:
    """Estimate occupancy rate from market signals and tourism demand."""
    comparables = state.get("comparables", [])
    total_reviews = sum(c.reviews or 0 for c in comparables)

    # Assume tourism area if we have many comparables with reviews
    is_tourism = total_reviews > 100 or len(comparables) >= 3
    saturation = 0.98 if len(comparables) > 10 else 1.0

    base_occ = estimate_occupancy(
        comparables,
        is_tourism_area=is_tourism,
        total_reviews=total_reviews,
        market_saturation_factor=saturation,
    )

    # Gather tourism demand signals and adjust
    signals = gather_tourism_signals(comparables)
    occ = adjust_occupancy_for_tourism(base_occ, signals)

    # Monthly occupancy curve (Jan-Dec)
    occupancy_curve = seasonal_occupancy_curve(occ)

    return {
        **state,
        "occupancy_rate": occ,
        "tourism_signals": signals,
        "occupancy_curve": occupancy_curve,
    }
