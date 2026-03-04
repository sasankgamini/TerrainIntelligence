"""PlannerAgent - breaks research into tasks and creates research plans."""
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState
from backend.models import ResearchPlan
from backend.models import PropertyInput

logger = logging.getLogger(__name__)


# Default research plan steps for glamping market analysis
DEFAULT_PLAN_STEPS = [
    {"id": "1", "action": "search_airbnb", "description": "Search Airbnb listings near property", "scraper": "airbnb"},
    {"id": "2", "action": "search_hipcamp", "description": "Search Hipcamp for glamping comparables", "scraper": "hipcamp"},
    {"id": "3", "action": "search_glampinghub", "description": "Search GlampingHub listings", "scraper": "glampinghub"},
    {"id": "4", "action": "search_google_maps", "description": "Check Google Maps campgrounds", "scraper": "google_maps"},
    {"id": "5", "action": "search_zillow", "description": "Gather Zillow market context", "scraper": "zillow"},
    {"id": "6", "action": "search_redfin", "description": "Gather Redfin market context", "scraper": "redfin"},
    {"id": "7", "action": "tourism_signals", "description": "Gather tourism demand signals", "scraper": "tourism"},
]


def create_research_plan(property_input: PropertyInput, doc_context: str = "") -> ResearchPlan:
    """
    Create a research plan for the property.
    Uses LLM if available for adaptive planning; otherwise returns default plan.
    """
    plan = ResearchPlan(
        property_address=property_input.property_address,
        steps=DEFAULT_PLAN_STEPS.copy(),
        current_step_index=0,
        completed_steps=[],
        websites_to_visit=[],
    )

    # Optionally use LLM to adapt plan based on doc_context
    if doc_context and "zoning" in doc_context.lower():
        plan.websites_to_visit.append("local zoning authority")
        logger.info("Planner: Added zoning context from documents")

    logger.info("Planner: Created research plan with %d steps", len(plan.steps))
    return plan


def planner_agent(state: AnalysisState) -> AnalysisState:
    """
    Break research into tasks and create a research plan.
    Decides which scrapers to run and which websites to visit.
    """
    prop = state.get("property_input")
    doc_context = state.get("doc_context", "")

    if not prop:
        logger.warning("Planner: No property input in state")
        return {**state, "error": "Missing property input"}

    plan = create_research_plan(prop, doc_context)

    # Initialize research_log if not present
    research_log = state.get("research_log", [])
    research_log.append({
        "agent": "planner",
        "action": "create_plan",
        "steps_count": len(plan.steps),
        "message": f"Created plan: {', '.join(s['action'] for s in plan.steps[:4])}...",
    })

    return {
        **state,
        "research_plan": plan,
        "research_log": research_log,
    }
