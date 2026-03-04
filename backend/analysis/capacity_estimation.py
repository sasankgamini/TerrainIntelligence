"""Capacity estimation based on acreage and zoning context."""
from dataclasses import dataclass
from typing import Optional


# Typical density: units per acre by type
CABINS_PER_ACRE = (2, 5)      # 2-5 per acre
GLAMPING_PER_ACRE = (4, 8)    # 4-8 per acre
RV_SITES_PER_ACRE = (6, 10)   # 6-10 per acre
TENT_SITES_PER_ACRE = (8, 15) # 8-15 per acre


@dataclass
class CapacityEstimate:
    """Estimated development capacity for a property."""
    max_cabins: int
    max_glamping: int
    max_rv_sites: int
    max_tent_sites: int
    total_units: int
    zoning_constraint: Optional[str] = None
    permitting_risk: str = "moderate"  # low, moderate, high


def estimate_capacity(
    acreage: float,
    doc_context: str = "",
    preferred_mix: Optional[dict] = None,
) -> CapacityEstimate:
    """
    Estimate maximum units for a property.
    Inputs: acreage, zoning context from uploaded documents, typical density.
    Rules:
    - Cabins: 2-5 per acre
    - Glamping tents: 4-8 per acre
    - RV sites: 6-10 per acre
    - Tent sites: 8-15 per acre
    """
    if acreage <= 0:
        return CapacityEstimate(0, 0, 0, 0, 0)

    # Default: equal split of acreage across unit types
    # Use midpoint of density ranges
    cabin_low, cabin_high = CABINS_PER_ACRE
    glamp_low, glamp_high = GLAMPING_PER_ACRE
    rv_low, rv_high = RV_SITES_PER_ACRE
    tent_low, tent_high = TENT_SITES_PER_ACRE

    # Zoning constraints from doc_context
    zoning_constraint = None
    permitting_risk = "moderate"
    density_multiplier = 1.0

    if doc_context:
        ctx_lower = doc_context.lower()
        if "restrictive" in ctx_lower or "limited" in ctx_lower or "low density" in ctx_lower:
            density_multiplier = 0.6
            permitting_risk = "moderate"
            zoning_constraint = "Documents suggest restrictive zoning"
        elif "high density" in ctx_lower or "commercial" in ctx_lower:
            density_multiplier = 1.2
            permitting_risk = "low"
        elif "wetland" in ctx_lower or "flood" in ctx_lower:
            density_multiplier = 0.5
            permitting_risk = "high"
            zoning_constraint = "Environmental constraints noted"

    # Allocate acreage: 25% each for cabins, glamping, RV, tent (simplified)
    acres_per_type = acreage / 4

    max_cabins = max(0, int(acres_per_type * (cabin_low + cabin_high) / 2 * density_multiplier))
    max_glamping = max(0, int(acres_per_type * (glamp_low + glamp_high) / 2 * density_multiplier))
    max_rv_sites = max(0, int(acres_per_type * (rv_low + rv_high) / 2 * density_multiplier))
    max_tent_sites = max(0, int(acres_per_type * (tent_low + tent_high) / 2 * density_multiplier))

    # Allow optimization of unit mix via preferred_mix
    if preferred_mix:
        if "cabins" in preferred_mix:
            max_cabins = min(max_cabins, preferred_mix["cabins"])
        if "glamping" in preferred_mix:
            max_glamping = min(max_glamping, preferred_mix["glamping"])
        if "rv" in preferred_mix:
            max_rv_sites = min(max_rv_sites, preferred_mix["rv"])
        if "tent" in preferred_mix:
            max_tent_sites = min(max_tent_sites, preferred_mix["tent"])

    total = max_cabins + max_glamping + max_rv_sites + max_tent_sites
    if total == 0:
        total = max(1, int(acreage * 2))  # Fallback: 2 units per acre
        max_glamping = total  # Default to glamping

    return CapacityEstimate(
        max_cabins=max_cabins,
        max_glamping=max_glamping,
        max_rv_sites=max_rv_sites,
        max_tent_sites=max_tent_sites,
        total_units=total,
        zoning_constraint=zoning_constraint,
        permitting_risk=permitting_risk,
    )
