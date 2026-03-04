"""PricingAgent - determines recommended nightly rate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.pricing_model import recommend_nightly_rate
from backend.analysis.comparable_filter import select_top_comparables


def pricing_agent(state: AnalysisState) -> AnalysisState:
    """Compute recommended nightly rate from top comparable listings."""
    prop = state["property_input"]
    comparables = state.get("comparables", [])
    override = prop.average_nightly_price_override

    # Select top 20 most similar comparables
    top_comparables = select_top_comparables(comparables, prop, top_n=20)
    filtered = [c for c, _ in top_comparables] if top_comparables else comparables

    rate = recommend_nightly_rate(filtered, override)
    return {
        **state,
        "recommended_nightly_rate": rate,
        "top_comparables": top_comparables if top_comparables else [(c, 0.5) for c in comparables[:20]],
    }
