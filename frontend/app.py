"""Streamlit UI for Glamping Market Research AI."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

from backend.models import PropertyInput
from backend.agents.graph import run_analysis
from backend.agents.property_scout_agent import scout_properties
from backend.models import ScoutInput
from backend.rag.retriever import DocumentRetriever

st.set_page_config(
    page_title="Glamping Market Research AI",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a5f2a;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #22c55e;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def _sync_api_keys_to_env():
    """Sync session state API keys to os.environ so backend reads them."""
    mapping = [
        ("OPENAI_API_KEY", "openai_api_key"),
        ("BROWSERBASE_API_KEY", "browserbase_api_key"),
        ("BROWSERBASE_PROJECT_ID", "browserbase_project_id"),
        ("OLLAMA_BASE_URL", "ollama_base_url"),
        ("MOCK_SCRAPING", "mock_scraping"),
    ]
    for env_key, session_key in mapping:
        val = st.session_state.get(session_key, "")
        if env_key == "MOCK_SCRAPING":
            if val:
                os.environ[env_key] = "1"
            else:
                os.environ.pop(env_key, None)
        elif val:
            os.environ[env_key] = str(val)
        else:
            os.environ.pop(env_key, None)


def main():
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = None
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if "browserbase_api_key" not in st.session_state:
        st.session_state.browserbase_api_key = os.getenv("BROWSERBASE_API_KEY", "")
    if "browserbase_project_id" not in st.session_state:
        st.session_state.browserbase_project_id = os.getenv("BROWSERBASE_PROJECT_ID", "")
    if "ollama_base_url" not in st.session_state:
        st.session_state.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    if "mock_scraping" not in st.session_state:
        st.session_state.mock_scraping = "1" if os.getenv("MOCK_SCRAPING", "").lower() in ("1", "true", "yes") else ""

    with st.sidebar:
        st.subheader("🔑 API Keys & Settings")
        with st.expander("Configure API Keys", expanded=False):
            st.caption("Enter your keys below. They are stored in your session only.")

            st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="Required for AI recommendations on cloud. Get one at platform.openai.com",
                key="openai_api_key",
            )

            st.divider()
            st.caption("Browserbase (optional – for live scraping instead of mock data)")

            st.text_input(
                "Browserbase API Key",
                type="password",
                placeholder="bb_...",
                key="browserbase_api_key",
            )

            st.text_input(
                "Browserbase Project ID",
                placeholder="Project ID",
                key="browserbase_project_id",
            )

            st.divider()
            st.caption("Ollama (optional – for local LLM instead of OpenAI)")

            st.text_input(
                "Ollama Base URL",
                placeholder="http://localhost:11434",
                key="ollama_base_url",
            )

            mock_checked = st.checkbox(
                "Use mock scraping (no browser)",
                value=bool(st.session_state.get("mock_scraping")),
                help="Use sample data instead of live scraping. Enable when no Browserbase.",
                key="mock_scraping_cb",
            )
            st.session_state.mock_scraping = "1" if mock_checked else ""

            if st.button("Save & Apply"):
                _sync_api_keys_to_env()
                st.success("Settings applied.")

    # Apply keys before any backend calls
    _sync_api_keys_to_env()

    st.markdown('<p class="main-header">🏕️ Glamping Market Research AI</p>', unsafe_allow_html=True)
    st.markdown("Analyze campground and glamping investment potential with AI-powered market research.")

    tab1, tab2, tab3 = st.tabs(["Market Analysis", "Land Investment Finder", "Export & Cache"])

    with tab1:
        render_market_analysis_tab()

    with tab2:
        render_scout_tab()

    with tab3:
        render_export_tab()


def render_market_analysis_tab():
    with st.form("analysis_form"):
        st.subheader("Property Inputs")
        col1, col2 = st.columns(2)

        with col1:
            property_address = st.text_input("Property Address", placeholder="e.g., Asheville, NC 28801")
            acreage = st.number_input("Acreage", min_value=0.0, value=10.0, step=0.5)
            number_of_cabins = st.number_input("Number of Cabins", min_value=0, value=2, step=1)
            number_of_glamping_units = st.number_input("Glamping Units", min_value=0, value=4, step=1)

        with col2:
            number_of_rv_sites = st.number_input("RV Sites", min_value=0, value=5, step=1)
            number_of_tent_sites = st.number_input("Tent Sites", min_value=0, value=10, step=1)
            average_nightly_override = st.number_input(
                "Override Avg Nightly Price (optional)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                help="Leave 0 to use AI-estimated pricing",
            )

        st.subheader("Upload Documents (zoning, reports, etc.)")
        uploaded_files = st.file_uploader(
            "PDF, DOCX, XLSX, TXT",
            type=["pdf", "docx", "xlsx", "txt"],
            accept_multiple_files=True,
        )

        submitted = st.form_submit_button("Run Market Analysis")

    if submitted and property_address:
        doc_context = ""
        if uploaded_files:
            try:
                retriever = DocumentRetriever()
                for f in uploaded_files:
                    retriever.add_uploaded_file(f)
                doc_context = retriever.retrieve("zoning regulations property restrictions", n=3)
            except Exception as e:
                st.warning(f"Document processing issue: {e}")

        prop_input = PropertyInput(
            property_address=property_address,
            acreage=acreage,
            number_of_cabins=number_of_cabins,
            number_of_glamping_units=number_of_glamping_units,
            number_of_rv_sites=number_of_rv_sites,
            number_of_tent_sites=number_of_tent_sites,
            average_nightly_price_override=average_nightly_override if average_nightly_override > 0 else None,
        )

        with st.spinner("Running market analysis (scraping, pricing, financials)..."):
            try:
                result = run_analysis(prop_input, doc_context)
                st.session_state.last_analysis = result
                display_analysis_results(result)
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.exception(e)
    elif submitted and not property_address:
        st.error("Please enter a property address.")


def display_analysis_results(state: dict):
    st.success("Analysis complete!")

    # Metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Recommended Rate", f"${state.get('recommended_nightly_rate', 0):.0f}/night")
    with c2:
        st.metric("Occupancy", f"{state.get('occupancy_rate', 0)*100:.1f}%")
    with c3:
        st.metric("Annual Revenue", f"${state.get('annual_revenue', 0):,.0f}")
    with c4:
        st.metric("ROI", f"{state.get('roi', 0):.1f}%")
    with c5:
        st.metric("Payback", f"{state.get('payback_period_years', 0):.1f} yrs")

    # Map and charts
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Comparables Map")
        comparables = state.get("comparables", [])
        if comparables:
            df = pd.DataFrame([
                {
                    "name": c.name,
                    "lat": 35.5,  # Placeholder - would use geocoding
                    "lon": -82.5,
                    "price": c.price_per_night,
                    "source": c.source,
                }
                for c in comparables if c.price_per_night > 0
            ])
            if not df.empty:
                st.map(df, latitude="lat", longitude="lon")
            else:
                st.info("No geocoded comparables. Install geopy for real coordinates.")
        else:
            st.info("No comparables to display.")

        st.subheader("Pricing Distribution")
        if comparables:
            prices = [c.price_per_night for c in comparables if c.price_per_night > 0]
            if prices:
                fig = px.histogram(x=prices, nbins=15, title="Nightly Rate Distribution")
                fig.update_layout(showlegend=False, xaxis_title="Price ($)", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No price data for chart.")
        else:
            st.info("No comparables.")

    with col_right:
        st.subheader("Expense Breakdown")
        exp = state.get("expense_breakdown", {})
        if exp:
            items = {k: v for k, v in exp.items() if k != "total" and isinstance(v, (int, float))}
            if items:
                fig = go.Figure(data=[go.Pie(labels=list(items.keys()), values=list(items.values()))])
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("10-Year Revenue Projection")
        proj = state.get("revenue_projection_10yr", [])
        if proj:
            df_proj = pd.DataFrame(proj)
            fig = px.line(df_proj, x="year", y="revenue", title="Revenue Over Time")
            fig.add_scatter(x=df_proj["year"], y=df_proj["expenses"], name="Expenses", mode="lines")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Investment Recommendation")
    st.markdown(state.get("recommendation", "N/A"))

    st.subheader("Full Report")
    report_md = state.get("report_markdown", "")
    st.markdown(report_md)

    # Download
    col1, col2, _ = st.columns([1, 1, 2])
    with col1:
        st.download_button(
            "Download Report (Markdown)",
            report_md,
            file_name="glamping_report.md",
            mime="text/markdown",
        )
    with col2:
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch

            buf = BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=letter)
            styles = getSampleStyleSheet()
            parts = []
            for block in report_md.split("\n\n"):
                block = block.strip()
                if not block:
                    continue
                # Strip markdown for simple PDF
                text = block.replace("**", "").replace("#", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "")
                text = text.replace("\n", "<br/>")[:2000]
                try:
                    parts.append(Paragraph(text, styles["Normal"]))
                    parts.append(Spacer(1, 0.2 * inch))
                except Exception:
                    parts.append(Paragraph(block[:500].replace("<", "&lt;").replace(">", "&gt;"), styles["Normal"]))
            if parts:
                doc.build(parts)
                pdf_bytes = buf.getvalue()
                st.download_button("Download Report (PDF)", pdf_bytes, file_name="glamping_report.pdf", mime="application/pdf")
            else:
                st.info("No content for PDF.")
        except Exception as e:
            st.info("PDF export: install reportlab. " + str(e))


def render_scout_tab():
    st.subheader("Land Investment Finder")
    st.markdown("Find properties with high glamping ROI potential.")

    with st.form("scout_form"):
        col1, col2 = st.columns(2)
        with col1:
            county = st.text_input("County", placeholder="e.g., Buncombe")
            state_name = st.text_input("State", placeholder="e.g., NC")
            min_acreage = st.number_input("Minimum Acreage", min_value=1.0, value=10.0, step=1.0)
        with col2:
            budget_min = st.number_input("Budget Min ($)", min_value=0, value=100000, step=10000)
            budget_max = st.number_input("Budget Max ($)", min_value=0, value=500000, step=10000)
            property_type = st.selectbox("Property Type", ["Land", "Ranch", "Farm", "Recreational"])

        scout_submitted = st.form_submit_button("Find Properties")

    if scout_submitted and county and state_name:
        scout_input = ScoutInput(
            county=county,
            state=state_name,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
            min_acreage=min_acreage,
            preferred_property_type=property_type,
        )
        with st.spinner("Scouting properties..."):
            try:
                results = scout_properties(scout_input)
                if results:
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                    st.subheader("Properties Map")
                    map_df = pd.DataFrame([
                        {"lat": 35.5, "lon": -82.5, "name": r["name"], "est_roi": r["est_roi"]}
                        for r in results[:10]
                    ])
                    st.map(map_df, latitude="lat", longitude="lon")
                else:
                    st.info("No properties found. Try broader search criteria.")
            except Exception as e:
                st.error(f"Scout failed: {e}")
                st.exception(e)
    elif scout_submitted:
        st.error("Please enter county and state.")


def render_export_tab():
    st.subheader("Export & Cache")
    st.markdown("Export comparables to CSV. Cache is stored in `data/cache/`.")

    if "last_analysis" in st.session_state and st.session_state.last_analysis:
        state = st.session_state.last_analysis
        comparables = state.get("comparables", [])
        if comparables:
            df = pd.DataFrame([
                {
                    "name": c.name,
                    "price_per_night": c.price_per_night,
                    "location": c.location,
                    "rating": c.rating,
                    "reviews": c.reviews,
                    "source": c.source,
                    "source_url": c.source_url,
                }
                for c in comparables
            ])
            csv = df.to_csv(index=False)
            st.download_button("Download Comparables (CSV)", csv, file_name="comparables.csv", mime="text/csv")
        else:
            st.info("No comparables in last analysis.")
    else:
        st.info("Run an analysis first to populate cache and enable CSV export.")


if __name__ == "__main__":
    main()
