import logging
import random

import allure
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.base_page import SEARCH_RESULTS_URL, BasePage
from utils.item_links import item_id
from utils.screenshots import capture_screenshot

logger = logging.getLogger(__name__)

# eBay's add to cart request sometimes takes well over the default 5s to answer.
ADD_TO_CART_TIMEOUT_MS = 30000


class ItemPage(BasePage):
    """Item pages, opened in their own tab so the search results tab never has to load again."""

    def __init__(self, page: Page, settings: Settings, search_tab: Page) -> None:
        super().__init__(page, settings)
        self.search_tab = search_tab
        self.variant_pickers = page.locator("[data-testid='x-msku-evo'] button.listbox-button__control")
        self.add_to_cart_button = page.get_by_role("button", name="Add to cart")
        self.added_to_cart_dialog = page.get_by_role("dialog", name="Added to cart")
        self.variant_errors = page.get_by_text("Please select a ")
        self.screenshots_dir = settings.artifacts_dir / "screenshots"

    def add_items_to_cart(self, urls: list[str]) -> None:
        """Adds each item to a cart that starts empty."""
        with allure.step(f"Add {len(urls)} items to the cart"):
            for already_added, url in enumerate(urls):
                self.add_item_to_cart(url, already_added)
                self.return_to_search_tab()

    @allure.step("Add {url} to the cart")
    def add_item_to_cart(self, url: str, already_added: int) -> None:
        self.open(url)
        self.verify_cart_count(already_added)
        self.select_random_variants()
        self.add_to_cart()
        self.verify_cart_count(already_added + 1)
        screenshot = capture_screenshot(self.page, f"item-{item_id(url)}", self.screenshots_dir)
        logger.info("Added %s to the cart, screenshot %s", url, screenshot)

    @allure.step("Open item {url}")
    def open(self, url: str) -> None:
        self.page.bring_to_front()
        self.visit(url)

    @allure.step("Click Add to cart")
    def click_add_to_cart(self) -> None:
        self.add_to_cart_button.click()

    @allure.step("Add the item to the cart")
    def add_to_cart(self) -> None:
        self.click_add_to_cart()
        expect(self.added_to_cart_dialog).to_be_visible(timeout=ADD_TO_CART_TIMEOUT_MS)

    @allure.step("Pick a random available value for every variant")
    def select_random_variants(self) -> list[str]:
        """Returns the picked values, e.g. ["Black", "US6.5/EU39"]."""
        picked = []
        for picker in self.variant_pickers.all():
            picker.click()
            listbox = self.page.locator(f"#{picker.get_attribute('aria-controls')}")
            available = listbox.locator("[role='option'][data-sku-value-name]:not([aria-disabled='true'])")
            available_count = available.count()
            if available_count == 0:
                raise AssertionError(f"No available value for variant '{picker.inner_text()}' on {self.page.url}")
            choice = available.nth(random.randrange(available_count))
            value = choice.get_attribute("data-sku-value-name") or ""
            choice.click()
            expect(picker).to_contain_text(value)
            logger.info("Variant picked: %s", value)
            picked.append(value)
        return picked

    @allure.step("Verify the added to cart dialog lists {values}")
    def verify_added_dialog_lists(self, values: list[str]) -> None:
        for value in values:
            expect(self.added_to_cart_dialog).to_contain_text(value)

    @allure.step("Verify every variant asks to be selected")
    def verify_variants_required(self) -> None:
        expect(self.variant_errors).to_have_count(self.variant_pickers.count())
        expect(self.added_to_cart_dialog).to_be_hidden()

    @allure.step("Return to the search results tab")
    def return_to_search_tab(self) -> None:
        self.search_tab.bring_to_front()
        expect(self.search_tab).to_have_url(SEARCH_RESULTS_URL)
