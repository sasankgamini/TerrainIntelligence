"""Financial model for ROI, NPV, IRR."""
from config import (
    CLEANING_COST_PER_TURN,
    BOOKING_PLATFORM_FEE,
    PROPERTY_TAX_RATE,
    INSURANCE_RATE,
    MAINTENANCE_RATE,
    MARKETING_RATE,
)


def total_units(cabins: int, glamping: int, rv_sites: int, tent_sites: int) -> int:
    return cabins + glamping + rv_sites + tent_sites


def annual_revenue(
    units: int,
    nightly_price: float,
    occupancy_rate: float,
) -> float:
    """Revenue = units × nightly_price × 365 × occupancy."""
    return units * nightly_price * 365 * occupancy_rate


def estimate_expenses(
    revenue: float,
    units: int,
    occupancy_rate: float,
    property_value: float = 0,
) -> dict:
    """Estimate yearly operating expenses."""
    turns_per_year = units * 365 * occupancy_rate * 0.9  # Approx. turns
    cleaning = turns_per_year * CLEANING_COST_PER_TURN
    platform_fees = revenue * BOOKING_PLATFORM_FEE
    marketing = revenue * MARKETING_RATE

    if property_value <= 0:
        property_value = revenue * 5  # Rough cap rate estimate

    property_tax = property_value * PROPERTY_TAX_RATE
    insurance = property_value * INSURANCE_RATE
    maintenance = property_value * MAINTENANCE_RATE

    # Staff: ~$15/hr part-time, 20 hrs/week
    staff = 15 * 20 * 52 * 0.5  # Half-time
    utilities = units * 120 * 12  # ~$120/unit/month

    total = cleaning + platform_fees + marketing + property_tax + insurance + maintenance + staff + utilities

    return {
        "cleaning": round(cleaning, 2),
        "platform_fees": round(platform_fees, 2),
        "marketing": round(marketing, 2),
        "property_tax": round(property_tax, 2),
        "insurance": round(insurance, 2),
        "maintenance": round(maintenance, 2),
        "staff": round(staff, 2),
        "utilities": round(utilities, 2),
        "total": round(total, 2),
    }


def noi(revenue: float, expenses: dict) -> float:
    return revenue - expenses["total"]


def roi(investment: float, noi_value: float) -> float:
    if investment <= 0:
        return 0.0
    return round(noi_value / investment * 100, 2)


def payback_period(investment: float, noi_value: float) -> float:
    if noi_value <= 0:
        return 999.0
    return round(investment / noi_value, 2)


def npv(cash_flows: list[float], discount_rate: float = 0.08) -> float:
    """NPV of cash flow stream."""
    total = 0.0
    for i, cf in enumerate(cash_flows):
        total += cf / (1 + discount_rate) ** i
    return round(total, 2)


def irr(cash_flows: list[float], guess: float = 0.1) -> float:
    """Approximate IRR via Newton-Raphson."""
    if not cash_flows or cash_flows[0] >= 0:
        return 0.0
    rate = guess
    for _ in range(100):
        npv_val = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-10:
            break
        rate = rate - npv_val / dnpv
        if rate < -0.99 or rate > 10:
            break
    return round(max(0, rate) * 100, 2)


# US camping seasonal factors (Jan-Dec): peak summer
SEASONAL_MONTHLY_FACTORS = [0.6, 0.55, 0.7, 0.85, 1.0, 1.1, 1.15, 1.1, 0.95, 0.8, 0.65, 0.6]

# Inflation assumption (annual)
DEFAULT_INFLATION_RATE = 0.03


def seasonal_occupancy_curve(base_occupancy: float) -> list[float]:
    """Monthly occupancy factors (Jan-Dec). Peak in summer."""
    return [base_occupancy * f for f in SEASONAL_MONTHLY_FACTORS]


def ten_year_projection(
    units: int,
    nightly_price: float,
    occupancy_rate: float,
    expenses: dict,
    growth_rate: float = 0.02,
    inflation_rate: float = DEFAULT_INFLATION_RATE,
) -> list[dict]:
    """Generate 10-year revenue/expense projection with inflation."""
    projection = []
    rev = annual_revenue(units, nightly_price, occupancy_rate)
    exp_total = expenses["total"]

    for year in range(1, 11):
        rev = rev * (1 + growth_rate) * (1 + inflation_rate * 0.5)  # Revenue grows + inflation
        exp_total = exp_total * (1 + growth_rate * 0.8) * (1 + inflation_rate)  # Expenses track inflation
        noi_val = rev - exp_total
        projection.append({
            "year": year,
            "revenue": round(rev, 2),
            "expenses": round(exp_total, 2),
            "noi": round(noi_val, 2),
        })
    return projection


def financial_scenarios(
    units: int,
    nightly_price: float,
    base_occupancy: float,
    expenses: dict,
    investment: float,
) -> dict:
    """
    Generate base, optimistic, and conservative financial scenarios.
    Returns dict with base_case, optimistic_case, conservative_case.
    """
    # Base case
    base_rev = annual_revenue(units, nightly_price, base_occupancy)
    base_noi = noi(base_rev, expenses)
    base_proj = ten_year_projection(units, nightly_price, base_occupancy, expenses, growth_rate=0.02)
    base_cf = [-investment] + [p["noi"] for p in base_proj]

    # Optimistic: +15% occupancy, +5% price, 3% growth
    opt_occ = min(0.75, base_occupancy * 1.15)
    opt_price = nightly_price * 1.05
    opt_rev = annual_revenue(units, opt_price, opt_occ)
    opt_exp = {**expenses, "total": expenses["total"] * 1.05}
    opt_noi = noi(opt_rev, opt_exp)
    opt_proj = ten_year_projection(units, opt_price, opt_occ, opt_exp, growth_rate=0.03)
    opt_cf = [-investment] + [p["noi"] for p in opt_proj]

    # Conservative: -15% occupancy, -5% price, 1% growth
    cons_occ = max(0.25, base_occupancy * 0.85)
    cons_price = nightly_price * 0.95
    cons_rev = annual_revenue(units, cons_price, cons_occ)
    cons_exp = {**expenses, "total": expenses["total"] * 0.95}
    cons_noi = noi(cons_rev, cons_exp)
    cons_proj = ten_year_projection(units, cons_price, cons_occ, cons_exp, growth_rate=0.01)
    cons_cf = [-investment] + [p["noi"] for p in cons_proj]

    return {
        "base_case": {
            "annual_revenue": base_rev,
            "noi": base_noi,
            "roi": roi(investment, base_noi),
            "npv": npv(base_cf),
            "irr": irr(base_cf),
            "payback_years": payback_period(investment, base_noi),
            "projection": base_proj,
            "cash_flows": base_cf,
        },
        "optimistic_case": {
            "annual_revenue": opt_rev,
            "noi": opt_noi,
            "roi": roi(investment, opt_noi),
            "npv": npv(opt_cf),
            "irr": irr(opt_cf),
            "payback_years": payback_period(investment, opt_noi),
            "projection": opt_proj,
            "cash_flows": opt_cf,
        },
        "conservative_case": {
            "annual_revenue": cons_rev,
            "noi": cons_noi,
            "roi": roi(investment, cons_noi),
            "npv": npv(cons_cf),
            "irr": irr(cons_cf),
            "payback_years": payback_period(investment, cons_noi),
            "projection": cons_proj,
            "cash_flows": cons_cf,
        },
    }
