"""Web scrapers for comparable listings."""
from .base_scraper import BaseScraper
from .airbnb_scraper import AirbnbScraper
from .hipcamp_scraper import HipcampScraper
from .glampinghub_scraper import GlampingHubScraper
from .google_maps_scraper import GoogleMapsScraper
from .zillow_scraper import ZillowScraper
from .redfin_scraper import RedfinScraper
from .landwatch_scraper import LandWatchScraper

__all__ = [
    "BaseScraper",
    "AirbnbScraper",
    "HipcampScraper",
    "GlampingHubScraper",
    "GoogleMapsScraper",
    "ZillowScraper",
    "RedfinScraper",
    "LandWatchScraper",
]
