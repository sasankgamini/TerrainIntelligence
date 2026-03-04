"""LangGraph workflow for market analysis."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langgraph.graph import StateGraph, END
from backend.agents.state import AnalysisState
from backend.agents.research_agent import research_agent
from backend.agents.pricing_agent import pricing_agent
from backend.agents.occupancy_agent import occupancy_agent
from backend.agents.expense_agent import expense_agent
from backend.agents.financial_agent import financial_agent
from backend.agents.report_agent import report_agent


def build_analysis_graph():
    """Build the LangGraph workflow."""
    workflow = StateGraph(AnalysisState)

    workflow.add_node("research", research_agent)
    workflow.add_node("pricing", pricing_agent)
    workflow.add_node("occupancy", occupancy_agent)
    workflow.add_node("expense", expense_agent)
    workflow.add_node("financial", financial_agent)
    workflow.add_node("report", report_agent)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "pricing")
    workflow.add_edge("pricing", "occupancy")
    workflow.add_edge("occupancy", "expense")
    workflow.add_edge("expense", "financial")
    workflow.add_edge("financial", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def run_analysis(property_input, doc_context: str = "") -> AnalysisState:
    """Run full analysis pipeline."""
    graph = build_analysis_graph()
    initial: AnalysisState = {
        "property_input": property_input,
        "doc_context": doc_context,
    }
    result = graph.invoke(initial)
    return result
