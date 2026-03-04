"""Data models for the market research platform."""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ComparableListing:
    """A comparable property listing from any source."""
    name: str
    price_per_night: float
    location: str
    distance_from_property: Optional[float] = None  # miles
    rating: Optional[float] = None
    reviews: Optional[int] = None
    amenities: list[str] = field(default_factory=list)
    unit_type: str = ""
    source: str = ""
    source_url: str = ""
    raw_data: dict = field(default_factory=dict)


@dataclass
class PropertyInput:
    """User input for property analysis."""
    property_address: str
    acreage: float
    number_of_cabins: int
    number_of_glamping_units: int
    number_of_rv_sites: int
    number_of_tent_sites: int
    average_nightly_price_override: Optional[float] = None


@dataclass
class ScoutInput:
    """User input for property scouting."""
    county: str
    state: str
    budget_min: float
    budget_max: float
    min_acreage: float
    preferred_property_type: str  # land, ranch, farm, etc.


@dataclass
class ResearchPlan:
    """Research plan created by PlannerAgent."""
    property_address: str
    steps: list[dict]  # {"id", "action", "description", "scraper"}
    current_step_index: int = 0
    completed_steps: list[str] = field(default_factory=list)
    websites_to_visit: list[str] = field(default_factory=list)


@dataclass
class VerifiedDataset:
    """Dataset with verification metadata."""
    comparables: list
    confidence_score: float  # 0-1
    source_count: int


@dataclass
class TourismDemandSignals:
    """Tourism demand signals from scraped sources."""
    review_counts: int
    attractions_nearby: int
    search_popularity_score: float  # 0-1
    sources: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    property_input: PropertyInput
    comparables: list[ComparableListing]
    recommended_nightly_rate: float
    occupancy_rate: float
    annual_revenue: float
    annual_expenses: float
    net_operating_income: float
    roi: float
    payback_period_years: float
    npv: float
    irr: float
    expense_breakdown: dict
    revenue_projection_10yr: list[dict]
    recommendation: str
    report_markdown: str
    created_at: datetime = field(default_factory=datetime.now)
