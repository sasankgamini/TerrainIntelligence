"""PricingAgent - determines recommended nightly rate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.pricing_model import recommend_nightly_rate


def pricing_agent(state: AnalysisState) -> AnalysisState:
    """Compute recommended nightly rate from comparables."""
    prop = state["property_input"]
    comparables = state.get("comparables", [])
    override = prop.average_nightly_price_override

    rate = recommend_nightly_rate(comparables, override)
    return {**state, "recommended_nightly_rate": rate}
