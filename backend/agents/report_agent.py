"""ReportAgent - generates full investment report."""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.state import AnalysisState


def _format_comparables(comparables: list, with_citations: bool = True) -> str:
    """Format comparables with automated source citations: [Name] – price – source URL."""
    lines = []
    for c in comparables[:20]:
        price = f"${c.price_per_night:.0f}/night" if c.price_per_night else "N/A"
        if with_citations and c.source_url:
            lines.append(f"- [{c.name}]({c.source_url}) – {price} – *{c.source}*")
        else:
            lines.append(f"- **{c.name}** ({c.source}): {price} | [Link]({c.source_url})")
    return "\n".join(lines) if lines else "No comparables found."


def _format_expenses(exp: dict) -> str:
    lines = []
    for k, v in exp.items():
        if k != "total" and isinstance(v, (int, float)):
            lines.append(f"- {k.replace('_', ' ').title()}: ${v:,.0f}")
    lines.append(f"- **Total**: ${exp.get('total', 0):,.0f}")
    return "\n".join(lines)


def _format_pricing_distribution(comparables: list) -> str:
    """Summarize comparable pricing distribution."""
    prices = [c.price_per_night for c in comparables if c.price_per_night and c.price_per_night > 0]
    if not prices:
        return "Insufficient price data."
    import numpy as np
    p25, p50, p75 = np.percentile(prices, [25, 50, 75])
    return f"25th: ${p25:.0f} | Median: ${p50:.0f} | 75th: ${p75:.0f}"


def report_agent(state: AnalysisState) -> AnalysisState:
    """Generate full investment report in Markdown."""
    prop = state["property_input"]
    comparables = state.get("comparables", [])
    rate = state.get("recommended_nightly_rate", 0)
    occ = state.get("occupancy_rate", 0)
    rev = state.get("annual_revenue", 0)
    exp = state.get("expense_breakdown", {})
    noi_val = state.get("net_operating_income", 0)
    roi_pct = state.get("roi", 0)
    payback = state.get("payback_period_years", 0)
    npv_val = state.get("npv", 0)
    irr_val = state.get("irr", 0)
    projection = state.get("revenue_projection_10yr", [])
    doc_context = state.get("doc_context", "")
    tourism = state.get("tourism_signals")
    verified = state.get("verified_dataset")
    scenarios = state.get("financial_scenarios", {})
    capacity = state.get("capacity_estimate")
    investment_score = state.get("investment_score", 0)

    units = (
        prop.number_of_cabins
        + prop.number_of_glamping_units
        + prop.number_of_rv_sites
        + prop.number_of_tent_sites
    )

    recommendation = _generate_recommendation(state)

    md = f"""# Glamping Investment Report
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 1. Property Overview

| Field | Value |
|-------|-------|
| Address | {prop.property_address} |
| Acreage | {prop.acreage} acres |
| Cabins | {prop.number_of_cabins} |
| Glamping Units | {prop.number_of_glamping_units} |
| RV Sites | {prop.number_of_rv_sites} |
| Tent Sites | {prop.number_of_tent_sites} |
| **Total Units** | {units} |

{f"### Uploaded Document Context\\n{doc_context}\\n" if doc_context else ""}

---

## 2. Market Comparables

{_format_comparables(comparables)}

---

## 3. Comparable Pricing Distribution

{_format_pricing_distribution(comparables)}

---

## 4. Tourism Demand Analysis

{f"- **Review counts**: {tourism.review_counts} across comparables" if tourism else "- No tourism data"}
{f"- **Attractions nearby**: {tourism.attractions_nearby} (estimated)" if tourism else ""}
{f"- **Search popularity**: {tourism.search_popularity_score:.0%}" if tourism else ""}
{f"- **Sources**: {', '.join(tourism.sources)}" if tourism and tourism.sources else ""}
{f"These signals support an occupancy estimate of {occ*100:.1f}%." if tourism else ""}

---

## 5. Market Competition

{f"**{len(comparables)}** comparable listings found across **{verified.source_count}** sources. Confidence: {verified.confidence_score:.0%}." if verified else f"**{len(comparables)}** comparable listings found."}

---

## 6. Development Capacity Estimate

{f"**Max capacity**: {capacity.total_units} units (Cabins: {capacity.max_cabins}, Glamping: {capacity.max_glamping}, RV: {capacity.max_rv_sites}, Tent: {capacity.max_tent_sites})" if capacity else ""}
{f"**Permitting risk**: {capacity.permitting_risk}" if capacity else ""}
{f"**Note**: {capacity.zoning_constraint}" if capacity and capacity.zoning_constraint else ""}

---

## 7. Pricing Analysis

| Metric | Value |
|--------|-------|
| Recommended Nightly Rate | ${rate:.2f} |
| Occupancy Estimate | {occ*100:.1f}% |

---

## 8. Revenue Forecast

| Metric | Value |
|--------|-------|
| Annual Revenue | ${rev:,.0f} |
| Formula | {units} units × ${rate:.0f}/night × 365 × {occ*100:.0f}% |

### 10-Year Projection

| Year | Revenue | Expenses | NOI |
|------|---------|----------|-----|
"""
    for p in projection:
        md += f"| {p['year']} | ${p['revenue']:,.0f} | ${p['expenses']:,.0f} | ${p['noi']:,.0f} |\n"

    md += f"""
---

## 9. Expense Breakdown

{_format_expenses(exp)}

---

## 10. Financial Scenarios

| Scenario | ROI | NPV | IRR | Payback |
|----------|-----|-----|-----|---------|
"""
    if scenarios:
        for name, data in [("Base", scenarios.get("base_case", {})), ("Optimistic", scenarios.get("optimistic_case", {})), ("Conservative", scenarios.get("conservative_case", {}))]:
            if data:
                md += f"| {name} | {data.get('roi', 0):.1f}% | ${data.get('npv', 0):,.0f} | {data.get('irr', 0):.1f}% | {data.get('payback_years', 0):.1f} yrs |\n"

    md += f"""
---

## 11. ROI Analysis

| Metric | Value |
|--------|-------|
| Net Operating Income | ${noi_val:,.0f} |
| ROI | {roi_pct}% |
| Payback Period | {payback:.1f} years |
| NPV (8% discount) | ${npv_val:,.0f} |
| IRR | {irr_val}% |
| **Investment Score** | {investment_score}/100 |

---

## 12. Investment Risk Assessment

- **Capacity risk**: {capacity.permitting_risk if capacity else "Unknown"} permitting risk
- **Market risk**: Based on {len(comparables)} comparables
- **Scenario spread**: See Base/Optimistic/Conservative above

---

## 13. Investment Recommendation

{recommendation}

---

*Report generated by Glamping Market Research AI. Sources linked above.*
"""

    return {**state, "report_markdown": md, "recommendation": recommendation}


def _generate_recommendation(state: AnalysisState) -> str:
    """Use LLM (OpenAI or Ollama) for recommendation if available."""
    roi_pct = state.get("roi", 0)
    payback = state.get("payback_period_years", 999)
    npv_val = state.get("npv", 0)

    prompt = f"""Based on these investment metrics, write a 2-3 sentence investment recommendation:
- ROI: {roi_pct}%
- Payback period: {payback} years
- NPV: ${npv_val:,.0f}

Be concise and actionable. Mention risk factors if ROI is low or payback is long."""

    # Try OpenAI first (works on cloud deployments)
    from config import get_openai_api_key

    api_key = get_openai_api_key()
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            if resp.choices and resp.choices[0].message.content:
                return resp.choices[0].message.content.strip()
        except Exception:
            pass

    # Try Ollama (local)
    try:
        import ollama
        from config import get_ollama_base_url, get_ollama_model

        client = ollama.Client(host=get_ollama_base_url())
        resp = client.generate(model=get_ollama_model(), prompt=prompt)
        if resp and hasattr(resp, "response") and resp.response:
            return resp.response.strip()
    except Exception:
        pass

    # Fallback
    if roi_pct >= 10 and payback < 15:
        return "**Favorable.** ROI and payback period suggest solid investment potential. Proceed with due diligence on zoning and permits."
    elif roi_pct >= 5:
        return "**Moderate.** Returns are acceptable. Consider cost reductions or revenue optimization to improve metrics."
    else:
        return "**Cautious.** ROI is below typical targets. Review assumptions on occupancy and pricing, or consider alternative uses."
