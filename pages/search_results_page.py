import logging
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode

import allure
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.base_page import BasePage, query_param_pattern
from utils.item_links import canonical_item_url
from utils.prices import PriceRange, parse_price_range

SEARCH_PATH = "/sch/i.html"
# Real result cards have id="item<hex>", eBay's "Shop on eBay" placeholder cards have an empty one.
RESULT_CARD_XPATH = "//ul[contains(@class,'srp-results')]/li[contains(@class,'s-card') and starts-with(@id,'item')]"
CARD_LINK_XPATH = ".//a[contains(@href,'/itm/')]"
# The row holding a card's price spans, a variation range is three of them: "ILS 20.00", " to ", "ILS 45.00".
CARD_PRICE_ROW_XPATH = ".//span[contains(@class,'s-card__price')]/.."
# Reads every card's price row text and item link with the XPaths above, in one call instead of two per card.
READ_CARDS_SCRIPT = """(cards, [priceRowXpath, linkXpath]) => cards.map(card => {
    const first = xpath =>
        document.evaluate(xpath, card, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
    return { price: first(priceRowXpath)?.innerText ?? '', href: first(linkXpath)?.getAttribute('href') ?? '' };
})"""

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultCard:
    url: str
    price: PriceRange

    @property
    def has_variants(self) -> bool:
        # Only listings with variants show a price range.
        return self.price.low != self.price.high


def whole_price(price: Decimal) -> int:
    # eBay's price filter only takes whole numbers, rounding up keeps every item priced at most `price`.
    return math.ceil(price)


def max_price_chip_pattern(whole_max_price: int) -> re.Pattern[str]:
    """Matches the applied filter chip, e.g. "Under ILS 220.00" or "Under $1,000.00"."""
    return re.compile(rf"Under \D*{re.escape(f'{whole_max_price:,}.00')}")


class SearchResultsPage(BasePage):
    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.result_cards = page.locator(f"xpath={RESULT_CARD_XPATH}")
        self.results_heading = page.locator(".srp-controls__count-heading")
        self.no_matches_message = page.locator(".srp-save-null-search__heading")
        self.applied_filters = page.locator("li.srp-multi-aspect__item--applied")
        price_range = page.locator(".su-price-filter .su-textrange")
        self.max_price_input = price_range.get_by_label(f"Maximum Value in {settings.currency}")
        self.submit_price_button = price_range.get_by_role("button", name="Submit price range")
        self.next_page_link = page.locator("a.pagination__next")

    @allure.step("Open the results for '{query}'")
    def open_results(self, query: str, max_price: Decimal | None = None, buy_it_now: bool = False) -> None:
        params: dict[str, object] = {"_nkw": query}
        if max_price is not None:
            params["_udhi"] = whole_price(max_price)
        if buy_it_now:
            params["LH_BIN"] = 1
        self.visit(f"{self.settings.base_url}{SEARCH_PATH}?{urlencode(params)}")

    @allure.step("Search '{query}' for up to {limit} items priced at most {max_price}")
    def search_items_by_name_under_price(self, query: str, max_price: Decimal, limit: int = 5) -> list[str]:
        # Buy It Now only, since auction listings have no "Add to cart" button.
        self.open_results(query, max_price, buy_it_now=True)
        urls: list[str] = []
        page_number = 1
        while True:
            urls += self.collect_items_under_price(max_price, limit - len(urls), already_collected=urls)
            out_of_pages = page_number == self.settings.max_result_pages or not self.has_next_page()
            if len(urls) == limit or out_of_pages:
                logger.info("Collected %d of %d items over %d page(s)", len(urls), limit, page_number)
                return urls
            page_number += 1
            self.go_to_page(page_number)

    @allure.step("Filter prices to at most {max_price}")
    def filter_max_price(self, max_price: Decimal) -> None:
        self.max_price_input.fill(str(whole_price(max_price)))
        self.submit_price_button.click()
        self.wait_for_page(query_param_pattern("_udhi", whole_price(max_price)))

    def read_cards(self) -> list[ResultCard]:
        cards = self.result_cards.evaluate_all(READ_CARDS_SCRIPT, [CARD_PRICE_ROW_XPATH, CARD_LINK_XPATH])
        result_cards = []
        for card in cards:
            price = parse_price_range(card["price"])
            self.require_currency(price.high)
            result_cards.append(ResultCard(canonical_item_url(card["href"], self.settings.base_url), price))
        return result_cards

    @allure.step("Collect up to {wanted} items priced at most {max_price} from this page")
    def collect_items_under_price(self, max_price: Decimal, wanted: int, already_collected: list[str]) -> list[str]:
        collected: list[str] = []
        for card in self.read_cards():
            if len(collected) == wanted:
                break
            # A range counts by its top price, since any variant may be picked later.
            if card.price.high.amount <= max_price and card.url not in already_collected + collected:
                collected.append(card.url)
                logger.info("Picked %s at %s", card.url, card.price.high)
        return collected

    def has_next_page(self) -> bool:
        return self.next_page_link.count() > 0

    @allure.step("Go to results page {page_number}")
    def go_to_page(self, page_number: int) -> None:
        self.next_page_link.click()
        self.wait_for_page(query_param_pattern("_pgn", page_number))

    @allure.step("Verify results page {page_number} is shown")
    def verify_page_number(self, page_number: int) -> None:
        expect(self.page).to_have_url(query_param_pattern("_pgn", page_number))

    @allure.step("Verify there are no results for '{query}'")
    def verify_no_results_for(self, query: str) -> None:
        expect(self.results_heading).to_have_text(f"0 results for {query}")
        expect(self.no_matches_message).to_have_text("No exact matches found")
        expect(self.result_cards).to_have_count(0)

    @allure.step("Verify every listing starts at most at {max_price}")
    def verify_max_price_filter(self, max_price: Decimal) -> None:
        whole_max_price = whole_price(max_price)
        expect(self.page).to_have_url(query_param_pattern("_udhi", whole_max_price))
        expect(self.applied_filters).to_contain_text(max_price_chip_pattern(whole_max_price))
        # eBay filters a range by its low price, so a range may still end above the max.
        too_expensive = [card for card in self.read_cards() if card.price.low.amount > whole_max_price]
        assert not too_expensive, f"Listings above {whole_max_price}: {too_expensive}"
