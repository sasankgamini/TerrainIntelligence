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


def ten_year_projection(
    units: int,
    nightly_price: float,
    occupancy_rate: float,
    expenses: dict,
    growth_rate: float = 0.02,
) -> list[dict]:
    """Generate 10-year revenue/expense projection."""
    projection = []
    rev = annual_revenue(units, nightly_price, occupancy_rate)
    exp_total = expenses["total"]

    for year in range(1, 11):
        rev = rev * (1 + growth_rate)
        exp_total = exp_total * (1 + growth_rate * 0.8)  # Expenses grow slower
        noi_val = rev - exp_total
        projection.append({
            "year": year,
            "revenue": round(rev, 2),
            "expenses": round(exp_total, 2),
            "noi": round(noi_val, 2),
        })
    return projection
