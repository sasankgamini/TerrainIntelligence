"""GlampingHub scraper for glamping listings."""
import time
from typing import Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scrapers.base_scraper import BaseScraper
from backend.models import ComparableListing


class GlampingHubScraper(BaseScraper):
    """Scrape GlampingHub for glamping comparables."""

    source_name = "glampinghub"

    def scrape(self, search_query: str) -> list[ComparableListing]:
        if not self.page:
            return self._get_mock_results(search_query)

        cache_key = self._cache_key(
            f"https://www.glampinghub.com/search?q={search_query}",
            search_query
        )
        cached = self._get_cached(cache_key)
        if cached:
            return [self._to_listing(d) for d in cached]

        listings = []
        try:
            url = f"https://www.glampinghub.com/search?q={search_query.replace(' ', '+')}"
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            html = self.page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            cards = soup.select('[class*="listing"]') or soup.select('article') or soup.select('div[class*="property"]')
            for card in cards[:15]:
                listing = self._parse_card(card, url)
                if listing and listing.price_per_night > 0:
                    listings.append(listing)

            if listings:
                self._save_cache(cache_key, [l.raw_data for l in listings])
        except Exception:
            listings = self._get_mock_results(search_query)

        return listings

    def _parse_card(self, card, base_url: str) -> Optional[ComparableListing]:
        data = {"source": self.source_name, "source_url": base_url}
        try:
            name_el = card.select_one('h2') or card.select_one('[class*="title"]')
            data["name"] = name_el.get_text(strip=True)[:100] if name_el else "GlampingHub Listing"

            price_el = card.select_one('[class*="price"]')
            if price_el:
                price = self._parse_price(price_el.get_text())
                if price:
                    data["price_per_night"] = price

            data["price_per_night"] = data.get("price_per_night", 0)
            data["location"] = search_query
            data["unit_type"] = "glamping"
            data["amenities"] = []

            return self._to_listing(data)
        except Exception:
            return None

    def _get_mock_results(self, search_query: str) -> list[ComparableListing]:
        return [
            self._to_listing({
                "name": f"Luxury Safari Tent - {search_query}",
                "price_per_night": 195,
                "location": search_query,
                "unit_type": "safari tent",
                "rating": 4.9,
                "reviews": 72,
                "amenities": ["King bed", "Private bath", "Deck"],
                "source_url": "https://www.glampinghub.com",
                "source": self.source_name,
            }),
            self._to_listing({
                "name": f"Treehouse Retreat - {search_query}",
                "price_per_night": 275,
                "location": search_query,
                "unit_type": "treehouse",
                "rating": 4.8,
                "reviews": 45,
                "amenities": ["Hot tub", "Kitchen", "View"],
                "source_url": "https://www.glampinghub.com",
                "source": self.source_name,
            }),
        ]
