"""Redfin scraper for land/property listings."""
import time
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scrapers.base_scraper import BaseScraper
from backend.models import ComparableListing


class RedfinScraper(BaseScraper):
    """Scrape Redfin for land/property comparables."""

    source_name = "redfin"

    def scrape(self, search_query: str) -> list[ComparableListing]:
        if not self.page:
            return self._get_mock_results(search_query)

        cache_key = self._cache_key(
            f"https://www.redfin.com/search?q={search_query}",
            search_query
        )
        cached = self._get_cached(cache_key)
        if cached:
            return [self._to_listing(d) for d in cached]

        listings = []
        try:
            url = f"https://www.redfin.com/search?q={search_query.replace(' ', '+')}"
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            html = self.page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            cards = soup.select('[data-rf-test-id="property-row"]') or soup.select('div[class*="HomeCard"]') or soup.select('a[href*="/home/"]')
            for card in cards[:15]:
                listing = self._parse_card(card, url)
                if listing:
                    listings.append(listing)

            if listings:
                self._save_cache(cache_key, [l.raw_data for l in listings])
        except Exception:
            listings = self._get_mock_results(search_query)

        return listings

    def _parse_card(self, card, base_url: str) -> Optional[ComparableListing]:
        data = {"source": self.source_name, "source_url": base_url}
        try:
            name_el = card.select_one('span[class*="streetAddress"]') or card.select_one('a') or card.select_one('div[class*="address"]')
            data["name"] = name_el.get_text(strip=True)[:100] if name_el else "Redfin Listing"

            price_el = card.select_one('span[class*="price"]') or card.select_one('[data-rf-test-id="price"]')
            if price_el:
                price = self._parse_price(price_el.get_text())
                if price and price < 10000:
                    data["price_per_night"] = price
                elif price:
                    data["price_per_night"] = price / 365 * 0.6
            data["price_per_night"] = data.get("price_per_night", 0)
            data["location"] = search_query
            data["unit_type"] = "land/property"
            data["amenities"] = []
            return self._to_listing(data)
        except Exception:
            return None

    def _get_mock_results(self, search_query: str) -> list[ComparableListing]:
        return [
            self._to_listing({
                "name": f"Property - {search_query}",
                "price_per_night": 0,
                "location": search_query,
                "unit_type": "land",
                "rating": None,
                "reviews": None,
                "amenities": [],
                "source_url": "https://www.redfin.com",
                "source": self.source_name,
            }),
        ]
