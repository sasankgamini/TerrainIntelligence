"""FinancialAgent - computes ROI, NPV, IRR, projections."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.analysis.financial_model import (
    total_units,
    annual_revenue,
    noi,
    roi,
    payback_period,
    npv,
    irr,
    ten_year_projection,
)


def financial_agent(state: AnalysisState) -> AnalysisState:
    """Compute ROI metrics and 10-year projection."""
    prop = state["property_input"]
    rate = state.get("recommended_nightly_rate", 150)
    occ = state.get("occupancy_rate", 0.5)
    expenses = state.get("expense_breakdown", {})
    rev = state.get("annual_revenue", 0)

    units = total_units(
        prop.number_of_cabins,
        prop.number_of_glamping_units,
        prop.number_of_rv_sites,
        prop.number_of_tent_sites,
    )
    if rev <= 0:
        rev = annual_revenue(units, rate, occ)

    noi_val = noi(rev, expenses)
    investment = rev * 5  # Assume 5x revenue as acquisition + development
    roi_pct = roi(investment, noi_val)
    payback = payback_period(investment, noi_val)

    projection = ten_year_projection(units, rate, occ, expenses)
    cash_flows = [-investment] + [p["noi"] for p in projection]
    npv_val = npv(cash_flows)
    irr_val = irr(cash_flows)

    return {
        **state,
        "net_operating_income": noi_val,
        "roi": roi_pct,
        "payback_period_years": payback,
        "npv": npv_val,
        "irr": irr_val,
        "revenue_projection_10yr": projection,
    }
