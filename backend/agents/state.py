"""Shared state for the analysis workflow."""
from typing import TypedDict, Optional, Any
from backend.models import PropertyInput, ComparableListing, AnalysisResult


class AnalysisState(TypedDict, total=False):
    """State passed between agents."""
    property_input: PropertyInput
    comparables: list[ComparableListing]
    recommended_nightly_rate: float
    occupancy_rate: float
    annual_revenue: float
    annual_expenses: float
    expense_breakdown: dict
    net_operating_income: float
    roi: float
    payback_period_years: float
    npv: float
    irr: float
    revenue_projection_10yr: list[dict]
    recommendation: str
    report_markdown: str
    doc_context: str
    error: Optional[str]
