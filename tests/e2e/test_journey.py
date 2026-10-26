import pytest

from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.item_page import ItemPage
from pages.search_results_page import SearchResultsPage
from utils.search_cases import SearchCase, load_search_cases

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("case", load_search_cases("journey"), ids=lambda case: case.id)
def test_cart_total_stays_within_budget(
    case: SearchCase,
    home_page: HomePage,
    search_results_page: SearchResultsPage,
    item_page: ItemPage,
    cart_page: CartPage,
) -> None:
    home_page.login_as_guest()
    urls = search_results_page.search_items_by_name_under_price(case.query, case.max_price, case.limit)
    item_page.add_items_to_cart(urls)
    cart_page.assert_cart_total_not_exceeds(case.max_price, len(urls))
