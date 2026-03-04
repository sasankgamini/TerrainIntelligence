"""Comparable filtering with weighted similarity scoring."""
import numpy as np
from backend.models import ComparableListing, PropertyInput


# Weights for similarity scoring (sum to 1.0)
WEIGHT_DISTANCE = 0.25
WEIGHT_UNIT_TYPE = 0.20
WEIGHT_AMENITIES = 0.15
WEIGHT_RATING = 0.20
WEIGHT_PRICE = 0.20

# Unit type similarity matrix (target unit -> comparable unit -> score 0-1)
UNIT_SIMILARITY = {
    "cabin": {"cabin": 1.0, "glamping": 0.8, "rv": 0.4, "tent": 0.3, "": 0.5},
    "glamping": {"glamping": 1.0, "cabin": 0.8, "rv": 0.5, "tent": 0.6, "": 0.5},
    "rv": {"rv": 1.0, "glamping": 0.5, "cabin": 0.4, "tent": 0.5, "": 0.5},
    "tent": {"tent": 1.0, "glamping": 0.6, "rv": 0.5, "cabin": 0.3, "": 0.5},
    "": {"": 0.5, "cabin": 0.5, "glamping": 0.5, "rv": 0.5, "tent": 0.5},
}


def _normalize_unit_type(unit_type: str) -> str:
    """Normalize unit type string for matching."""
    if not unit_type:
        return ""
    u = unit_type.lower()
    if "cabin" in u or "cottage" in u:
        return "cabin"
    if "glamp" in u or "yurt" in u or "safari" in u:
        return "glamping"
    if "rv" in u or "camper" in u:
        return "rv"
    if "tent" in u or "camp" in u:
        return "tent"
    return u[:20] if u else ""


def _get_primary_unit_type(prop: PropertyInput) -> str:
    """Get primary unit type from property (most units)."""
    counts = {
        "cabin": prop.number_of_cabins,
        "glamping": prop.number_of_glamping_units,
        "rv": prop.number_of_rv_sites,
        "tent": prop.number_of_tent_sites,
    }
    return max(counts, key=counts.get) if any(counts.values()) else ""


def _distance_score(distance_miles: float | None) -> float:
    """Score 0-1: closer = higher. None = 0.5 (unknown)."""
    if distance_miles is None:
        return 0.5
    if distance_miles <= 5:
        return 1.0
    if distance_miles <= 15:
        return 0.8
    if distance_miles <= 30:
        return 0.6
    if distance_miles <= 50:
        return 0.4
    return 0.2


def _price_similarity(comp_price: float, target_price: float) -> float:
    """Score 0-1: how similar is comp price to target. Target from median of comparables if 0."""
    if not comp_price or comp_price <= 0:
        return 0.5
    if target_price <= 0:
        return 0.5
    ratio = comp_price / target_price
    if 0.8 <= ratio <= 1.2:
        return 1.0
    if 0.6 <= ratio <= 1.5:
        return 0.8
    if 0.4 <= ratio <= 2.0:
        return 0.6
    return 0.3


def _rating_score(rating: float | None) -> float:
    """Score 0-1 from rating (assume 5-point scale)."""
    if rating is None:
        return 0.5
    return min(1.0, (rating or 0) / 5.0)


def _amenity_overlap(comp_amenities: list, target_amenities: list) -> float:
    """Score 0-1 from amenity overlap. Empty = 0.5."""
    if not comp_amenities and not target_amenities:
        return 0.5
    if not comp_amenities:
        return 0.3
    comp_set = set(a.lower() for a in comp_amenities)
    if not target_amenities:
        return 0.5 if comp_set else 0.3
    target_set = set(a.lower() for a in target_amenities)
    overlap = len(comp_set & target_set) / max(1, len(comp_set | target_set))
    return min(1.0, 0.5 + overlap * 0.5)


def compute_similarity_score(
    comp: ComparableListing,
    prop: PropertyInput,
    target_price: float = 0,
    target_amenities: list | None = None,
) -> float:
    """
    Compute weighted similarity score 0-1 for a comparable.
    Higher = more similar to target property.
    """
    primary = _get_primary_unit_type(prop)
    comp_unit = _normalize_unit_type(comp.unit_type)
    unit_sim = UNIT_SIMILARITY.get(primary, {}).get(comp_unit, 0.5)

    dist_score = _distance_score(comp.distance_from_property)
    rating_sc = _rating_score(comp.rating)
    amenity_sc = _amenity_overlap(comp.amenities or [], target_amenities or [])

    # Use median of comparables as target price if not provided
    price_sc = _price_similarity(comp.price_per_night, target_price) if target_price else 0.5

    score = (
        WEIGHT_DISTANCE * dist_score
        + WEIGHT_UNIT_TYPE * unit_sim
        + WEIGHT_AMENITIES * amenity_sc
        + WEIGHT_RATING * rating_sc
        + WEIGHT_PRICE * price_sc
    )
    return round(min(1.0, max(0, score)), 4)


def select_top_comparables(
    comparables: list[ComparableListing],
    prop: PropertyInput,
    top_n: int = 20,
    target_price: float = 0,
) -> list[tuple[ComparableListing, float]]:
    """
    Select top N most similar comparables using weighted scoring.
    Returns list of (listing, score) sorted by score descending.
    """
    if not comparables:
        return []

    if target_price <= 0:
        prices = [c.price_per_night for c in comparables if c.price_per_night and c.price_per_night > 0]
        target_price = float(np.median(prices)) if prices else 150

    scored = [
        (c, compute_similarity_score(c, prop, target_price))
        for c in comparables
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
