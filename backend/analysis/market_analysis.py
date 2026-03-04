"""Market analysis utilities."""
from backend.models import ComparableListing
import pandas as pd


def comparables_to_dataframe(listings: list[ComparableListing]) -> pd.DataFrame:
    """Convert listings to DataFrame for analysis."""
    rows = []
    for L in listings:
        rows.append({
            "name": L.name,
            "price_per_night": L.price_per_night,
            "location": L.location,
            "distance_miles": L.distance_from_property,
            "rating": L.rating,
            "reviews": L.reviews,
            "unit_type": L.unit_type,
            "source": L.source,
            "source_url": L.source_url,
            "amenities": ", ".join(L.amenities) if L.amenities else "",
        })
    return pd.DataFrame(rows)


def filter_valid_prices(df: pd.DataFrame, min_price: float = 20, max_price: float = 2000) -> pd.DataFrame:
    """Filter out invalid nightly prices."""
    return df[(df["price_per_night"] >= min_price) & (df["price_per_night"] <= max_price)]
