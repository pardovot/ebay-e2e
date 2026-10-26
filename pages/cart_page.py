import logging
from decimal import Decimal

import allure
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.base_page import BasePage
from utils.prices import parse_money
from utils.screenshots import capture_screenshot

logger = logging.getLogger(__name__)


def items_label(count: int) -> str:
    return f"Item ({count})" if count == 1 else f"Items ({count})"


class CartPage(BasePage):
    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        summary = page.locator("[data-test-id='cart-summary']")
        self.items_total = summary.locator("[data-test-id='ITEM_TOTAL']")
        self.items_line = self.items_total.locator("xpath=..")
        self.empty_cart_message = page.get_by_text("You don't have any items in your cart.")
        self.screenshots_dir = settings.artifacts_dir / "screenshots"

    @allure.step("Assert the cart items total is at most {budget_per_item} x {items_count}")
    def assert_cart_total_not_exceeds(self, budget_per_item: Decimal, items_count: int) -> None:
        self.visit(self.settings.cart_url)
        capture_screenshot(self.page, "cart", self.screenshots_dir)
        if items_count == 0:
            expect(self.empty_cart_message).to_be_visible()
            return
        expect(self.items_line).to_contain_text(items_label(items_count))
        # "Subtotal" on eBay includes shipping, so the budget is checked against the items line.
        items_total = parse_money(self.items_total.inner_text())
        self.require_currency(items_total)
        threshold = budget_per_item * items_count
        logger.info("Cart items total %s, threshold %s", items_total, threshold)
        assert items_total.amount <= threshold, f"Cart items total {items_total} exceeds {threshold}"
