"""Base scraper with common utilities."""
import json
import hashlib
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models import ComparableListing
from config import CACHE_DIR


class BaseScraper:
    """Base class for all scrapers."""

    source_name = "base"
    cache_ttl_hours = 24

    def __init__(self, page=None, property_location: Optional[str] = None):
        self.page = page
        self.property_location = property_location

    def _cache_key(self, url: str, extra: str = "") -> str:
        key = f"{self.source_name}:{url}:{extra}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[list[dict]]:
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def _save_cache(self, cache_key: str, data: list[dict]):
        cache_file = CACHE_DIR / f"{cache_key}.json"
        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def _parse_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text like '$150/night' or '$150'."""
        if not text:
            return None
        import re
        match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', text.replace(",", ""))
        if match:
            return float(match.group(1))
        return None

    def _to_listing(self, data: dict) -> ComparableListing:
        return ComparableListing(
            name=data.get("name", ""),
            price_per_night=data.get("price_per_night", 0),
            location=data.get("location", ""),
            distance_from_property=data.get("distance_from_property"),
            rating=data.get("rating"),
            reviews=data.get("reviews"),
            amenities=data.get("amenities", []),
            unit_type=data.get("unit_type", ""),
            source=self.source_name,
            source_url=data.get("source_url", ""),
            raw_data=data,
        )

    def scrape(self, search_query: str) -> list[ComparableListing]:
        """Override in subclasses. Returns list of ComparableListing."""
        raise NotImplementedError
