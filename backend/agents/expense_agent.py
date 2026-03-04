"""ExpenseAgent - estimates operating expenses."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.financial_model import (
    total_units,
    annual_revenue,
    estimate_expenses,
)


def expense_agent(state: AnalysisState) -> AnalysisState:
    """Estimate yearly operating expenses."""
    prop = state["property_input"]
    rate = state.get("recommended_nightly_rate", 150)
    occ = state.get("occupancy_rate", 0.5)

    units = total_units(
        prop.number_of_cabins,
        prop.number_of_glamping_units,
        prop.number_of_rv_sites,
        prop.number_of_tent_sites,
    )
    rev = annual_revenue(units, rate, occ)
    property_value = rev * 5  # Rough cap rate
    expenses = estimate_expenses(rev, units, occ, property_value)

    return {
        **state,
        "annual_revenue": rev,
        "expense_breakdown": expenses,
        "annual_expenses": expenses["total"],
    }
