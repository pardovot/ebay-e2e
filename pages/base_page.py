import re
from urllib.parse import quote_plus

import allure
from playwright.sync_api import Page, expect

from config.settings import Settings
from utils.prices import Money

BOT_WALL_TITLE = "Error Page | eBay"
BOT_WALL_MESSAGE = "eBay served its bot wall instead of the page"
# eBay's challenge page, which checks the browser and then redirects to the requested page by itself.
CHALLENGE_URL = re.compile(r"/splashui/challenge")
# eBay renders pages on the server, and its component script attaches their handlers about a second after load.
# Input before that is lost, a picked variant resets and a typed price never enables the price filter.
SCRIPTS_READY = "() => 'markoInitComponents' in window"
# Any search results URL, e.g. "https://www.ebay.com/sch/i.html?_nkw=shoes".
SEARCH_RESULTS_URL = re.compile(r"/sch/")


def cart_label(count: int) -> str:
    # eBay says "items" for every count, including 1.
    return f"Your shopping cart contains {count} items"


def query_param_pattern(name: str, value: object) -> re.Pattern[str]:
    """Matches a URL whose query string has exactly `name=value`, e.g. "_pgn=2" but not "_pgn=20"."""
    return re.compile(rf"[?&]{re.escape(name)}={re.escape(quote_plus(str(value)))}(&|$)")


class BasePage:
    """Navigation and the header cart icon shared by every eBay page."""

    def __init__(self, page: Page, settings: Settings) -> None:
        self.page = page
        self.settings = settings
        self.cart_link = page.locator(".gh-cart a.gh-flyout__target")
        self.captcha_heading = page.get_by_role("heading", name="Please verify yourself to continue")

    @allure.step("Open {url}")
    def visit(self, url: str) -> None:
        self.page.goto(url)
        self.wait_until_ready()

    def wait_for_page(self, url: str | re.Pattern[str]) -> None:
        """Waits for a navigation started by a click or key press, then for the page like visit()."""
        self.page.wait_for_url(url)
        self.wait_until_ready()

    def wait_until_ready(self) -> None:
        """Waits out eBay's challenge page, fails on its bot wall or captcha, then waits for the page's scripts."""
        self.page.wait_for_url(lambda current: not CHALLENGE_URL.search(current))
        expect(self.page, BOT_WALL_MESSAGE).not_to_have_title(BOT_WALL_TITLE)
        expect(self.captcha_heading, BOT_WALL_MESSAGE).to_be_hidden()
        self.page.wait_for_function(SCRIPTS_READY)

    @allure.step("Verify the header cart holds {count} items")
    def verify_cart_count(self, count: int) -> None:
        expect(self.cart_link).to_have_attribute("aria-label", cart_label(count))

    def require_currency(self, money: Money) -> None:
        if money.currency != self.settings.currency:
            raise AssertionError(
                f"eBay shows {money.currency} prices but the run expects {self.settings.currency}, "
                "set EBAY_CURRENCY to match"
            )
