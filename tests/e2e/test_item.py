import pytest

from pages.item_page import ItemPage
from pages.search_results_page import ResultCard

pytestmark = pytest.mark.e2e


def test_added_dialog_lists_random_variants(item_page: ItemPage, listing_with_variants: ResultCard) -> None:
    item_page.open(listing_with_variants.url)
    values = item_page.select_random_variants()
    item_page.add_to_cart()
    item_page.verify_added_dialog_lists(values)


def test_add_to_cart_requires_variants(item_page: ItemPage, listing_with_variants: ResultCard) -> None:
    item_page.open(listing_with_variants.url)
    item_page.click_add_to_cart()
    item_page.verify_variants_required()
    item_page.verify_cart_count(0)
