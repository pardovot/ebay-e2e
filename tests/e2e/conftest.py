from collections.abc import Generator
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from config.settings import Settings
from pages.address_dialog import AddressDialog
from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.item_page import ItemPage
from pages.search_results_page import ResultCard, SearchResultsPage
from utils.network import block_ads_arg
from utils.search_cases import load_search_cases

# The first flag stops Chromium from setting navigator.webdriver, the most basic bot signal. --lang keeps the
# Accept-Language header the same on every machine.
LAUNCH_ARGS = ["--disable-blink-features=AutomationControlled", "--lang=en-US"]
VIEWPORT = {"width": 1440, "height": 900}
# Allure type of each artifact pytest-playwright keeps, keyed by its report property.
PLAYWRIGHT_ARTIFACT_TYPES = {
    "playwright_screenshot": allure.attachment_type.PNG,
    "playwright_video": allure.attachment_type.WEBM,
    "playwright_trace": allure.attachment_type.ZIP,
}


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def browser_type_launch_args(settings: Settings) -> dict[str, object]:
    return {
        "headless": settings.headless,
        "slow_mo": settings.slow_mo_ms,
        "args": [*LAUNCH_ARGS, block_ads_arg()],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, object]) -> dict[str, object]:
    return {**browser_context_args, "viewport": VIEWPORT}


def open_tab(context: BrowserContext, settings: Settings) -> Page:
    tab = context.new_page()
    AddressDialog(tab, settings).dismiss_whenever_shown()
    return tab


@pytest.fixture
def page(context: BrowserContext, settings: Settings) -> Page:
    return open_tab(context, settings)


@pytest.fixture
def item_tab(context: BrowserContext, settings: Settings, page: Page) -> Page:
    tab = open_tab(context, settings)
    page.bring_to_front()
    return tab


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Generator[None]:
    """Attaches what pytest-playwright kept for the test, listed on its teardown report, to the Allure result."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "teardown":
        return
    for kind, path in report.user_properties:
        if kind in PLAYWRIGHT_ARTIFACT_TYPES:
            allure.attach.file(path, name=Path(path).name, attachment_type=PLAYWRIGHT_ARTIFACT_TYPES[kind])


@pytest.fixture
def home_page(page: Page, settings: Settings) -> HomePage:
    return HomePage(page, settings)


@pytest.fixture
def search_results_page(page: Page, settings: Settings) -> SearchResultsPage:
    return SearchResultsPage(page, settings)


@pytest.fixture
def item_page(item_tab: Page, settings: Settings, page: Page) -> ItemPage:
    return ItemPage(item_tab, settings, search_tab=page)


@pytest.fixture
def cart_page(page: Page, settings: Settings) -> CartPage:
    return CartPage(page, settings)


@pytest.fixture(scope="session")
def listings(browser: Browser, browser_context_args: dict[str, object], settings: Settings) -> list[ResultCard]:
    """Result cards of one search, shared by the item and cart tests so they don't search again."""
    case = load_search_cases("listings")[0]
    context = browser.new_context(**browser_context_args)
    try:
        results_page = SearchResultsPage(open_tab(context, settings), settings)
        results_page.open_results(case.query, case.max_price, buy_it_now=True)
        return results_page.read_cards()
    finally:
        context.close()


@pytest.fixture
def listing(listings: list[ResultCard]) -> ResultCard:
    return listings[0]


@pytest.fixture
def listing_with_variants(listings: list[ResultCard]) -> ResultCard:
    with_variants = [card for card in listings if card.has_variants]
    if not with_variants:
        pytest.fail("The listings search found no listing with variants")
    return with_variants[0]
