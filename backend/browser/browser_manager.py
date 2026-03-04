"""Browser manager - Browserbase or local Playwright."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from typing import Optional

try:
    from browserbase import Browserbase
except ImportError:
    Browserbase = None


def get_browser_manager():
    """Get the appropriate browser manager based on environment."""
    from config import use_browserbase, get_browserbase_api_key, get_browserbase_project_id

    if use_browserbase() and Browserbase:
        return BrowserbaseManager(get_browserbase_api_key(), get_browserbase_project_id())
    return LocalPlaywrightManager()


class BaseBrowserManager:
    """Base class for browser management."""

    def get_page(self) -> tuple[Page, "BaseBrowserManager"]:
        """Get a browser page. Returns (page, manager) - caller must call cleanup()."""
        raise NotImplementedError

    def cleanup(self):
        """Clean up browser resources."""
        raise NotImplementedError


class BrowserbaseManager(BaseBrowserManager):
    """Manage browser via Browserbase remote sessions."""

    def __init__(self, api_key: str, project_id: str):
        self.bb = Browserbase(api_key=api_key)
        self.project_id = project_id
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.session = None

    def get_page(self) -> tuple[Page, "BrowserbaseManager"]:
        session = self.bb.sessions.create(project_id=self.project_id)
        self.session = session

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(session.connect_url)
        context = self.browser.contexts[0]
        page = context.pages[0]
        return page, self

    def cleanup(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.playwright = None
        self.session = None


class LocalPlaywrightManager(BaseBrowserManager):
    """Manage local Playwright browser."""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

    def get_page(self) -> tuple[Page, "LocalPlaywrightManager"]:
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()
        return page, self

    def cleanup(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.playwright = None


def with_browser(func):
    """Decorator to provide a browser page to a function."""

    def wrapper(*args, **kwargs):
        manager = get_browser_manager()
        page, mgr = manager.get_page()
        try:
            return func(page, *args, **kwargs)
        finally:
            mgr.cleanup()

    return wrapper
