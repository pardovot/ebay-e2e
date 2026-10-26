import pytest

from pages.cart_page import CartPage
from pages.item_page import ItemPage
from pages.search_results_page import ResultCard

pytestmark = pytest.mark.e2e


def test_cart_total_over_budget_fails(item_page: ItemPage, cart_page: CartPage, listing: ResultCard) -> None:
    item_page.add_item_to_cart(listing.url, already_added=0)
    budget_below_price = listing.price.low.amount / 2

    with pytest.raises(AssertionError, match="exceeds"):
        cart_page.assert_cart_total_not_exceeds(budget_below_price, 1)
