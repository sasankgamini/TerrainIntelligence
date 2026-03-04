"""LangGraph workflow for market analysis with autonomous research loop."""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.agents.state import AnalysisState
from backend.agents.planner_agent import planner_agent
from backend.agents.browser_agent import browser_agent
from backend.agents.verifier_agent import verifier_agent
from backend.agents.research_agent import research_agent  # Fallback when not using autonomous loop
from backend.agents.pricing_agent import pricing_agent
from backend.agents.occupancy_agent import occupancy_agent
from backend.agents.expense_agent import expense_agent
from backend.agents.financial_agent import financial_agent
from backend.agents.report_agent import report_agent

logger = logging.getLogger(__name__)

# Research loop config
MIN_LISTINGS_SUFFICIENT = 15
MAX_RESEARCH_ITERATIONS = 3


def _should_continue_research(state: AnalysisState) -> str:
    """
    Route: continue to pricing if sufficient listings or max iterations reached.
    Otherwise loop back to planner.
    """
    comparables = state.get("comparables", [])
    iteration = state.get("iteration_count", 0)
    verified = state.get("verified_dataset")

    if verified and verified.confidence_score >= 0.7 and len(comparables) >= 10:
        return "pricing"
    if len(comparables) >= MIN_LISTINGS_SUFFICIENT:
        return "pricing"
    if iteration >= MAX_RESEARCH_ITERATIONS:
        logger.info("Research loop: max iterations (%d) reached, proceeding", MAX_RESEARCH_ITERATIONS)
        return "pricing"
    return "planner"


def _increment_iteration(state: AnalysisState) -> AnalysisState:
    """Increment research iteration when looping back."""
    it = state.get("iteration_count", 0) + 1
    return {**state, "iteration_count": it}


def build_analysis_graph(use_autonomous_research: bool = True):
    """
    Build the LangGraph workflow.
    If use_autonomous_research=True, uses planner->browser->verifier loop.
    Otherwise uses legacy single research_agent.
    """
    workflow = StateGraph(AnalysisState)

    if use_autonomous_research:
        workflow.add_node("planner", planner_agent)
        workflow.add_node("browser", browser_agent)
        workflow.add_node("verifier", verifier_agent)
        workflow.add_node("increment_iteration", _increment_iteration)

        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "browser")
        workflow.add_edge("browser", "verifier")
        workflow.add_conditional_edges(
            "verifier",
            _should_continue_research,
            {
                "planner": "increment_iteration",
                "pricing": "pricing",
            },
        )
        workflow.add_edge("increment_iteration", "browser")
    else:
        workflow.add_node("research", research_agent)
        workflow.set_entry_point("research")
        workflow.add_edge("research", "pricing")

    workflow.add_node("pricing", pricing_agent)
    workflow.add_node("occupancy", occupancy_agent)
    workflow.add_node("expense", expense_agent)
    workflow.add_node("financial", financial_agent)
    workflow.add_node("report", report_agent)

    workflow.add_edge("pricing", "occupancy")
    workflow.add_edge("occupancy", "expense")
    workflow.add_edge("expense", "financial")
    workflow.add_edge("financial", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def run_analysis(property_input, doc_context: str = "", use_autonomous_research: bool = True) -> AnalysisState:
    """Run full analysis pipeline with optional autonomous research loop."""
    graph = build_analysis_graph(use_autonomous_research=use_autonomous_research)
    initial: AnalysisState = {
        "property_input": property_input,
        "doc_context": doc_context,
        "iteration_count": 0,
    }
    result = graph.invoke(initial)
    return result
