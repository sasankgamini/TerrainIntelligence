"""Shared state for the analysis workflow."""
from typing import TypedDict, Optional, Any
from backend.models import PropertyInput, ComparableListing, AnalysisResult, ResearchPlan, VerifiedDataset, TourismDemandSignals


class AnalysisState(TypedDict, total=False):
    """State passed between agents."""
    property_input: PropertyInput
    research_plan: ResearchPlan
    research_log: list[dict]
    iteration_count: int
    comparables: list[ComparableListing]
    verified_dataset: VerifiedDataset
    tourism_signals: TourismDemandSignals
    occupancy_curve: list[float]
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
    financial_scenarios: dict
    capacity_estimate: Any
    top_comparables: list
    recommendation: str
    report_markdown: str
    doc_context: str
    investment_score: float
    error: Optional[str]
