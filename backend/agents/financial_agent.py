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
    financial_scenarios,
)
from backend.analysis.capacity_estimation import estimate_capacity


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

    scenarios = financial_scenarios(units, rate, occ, expenses, investment)
    capacity_estimate = estimate_capacity(prop.acreage, state.get("doc_context", ""))

    state_with_metrics = {
        **state,
        "net_operating_income": noi_val,
        "roi": roi_pct,
        "payback_period_years": payback,
        "npv": npv_val,
        "irr": irr_val,
        "revenue_projection_10yr": projection,
        "financial_scenarios": scenarios,
        "capacity_estimate": capacity_estimate,
    }
    roi_weight = min(1.0, roi_pct / 15) * 0.35
    tourism = state.get("tourism_signals")
    demand_weight = (tourism.search_popularity_score if tourism else 0.5) * 0.25
    comp_count = len(state.get("comparables", []))
    competition_weight = min(1.0, comp_count / 20) * 0.2
    tourism_weight = (tourism.search_popularity_score if tourism else 0.5) * 0.2
    state_with_metrics["investment_score"] = round(
        (roi_weight + demand_weight + (1 - competition_weight * 0.5) + tourism_weight) * 100, 1
    )
    return state_with_metrics
