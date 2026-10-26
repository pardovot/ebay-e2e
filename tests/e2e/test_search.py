import pytest

from pages.search_results_page import SearchResultsPage
from utils.search_cases import SearchCase, load_search_cases

pytestmark = pytest.mark.e2e

SECOND_PAGE = 2


def case_id(case: SearchCase) -> str:
    return case.id


@pytest.mark.parametrize("case", load_search_cases("limits"), ids=case_id)
def test_search_returns_up_to_limit(case: SearchCase, search_results_page: SearchResultsPage) -> None:
    urls = search_results_page.search_items_by_name_under_price(case.query, case.max_price, case.limit)

    assert len(urls) == case.limit
    assert len(set(urls)) == len(urls), "the same listing was collected twice"


@pytest.mark.parametrize("case", load_search_cases("paging"), ids=case_id)
def test_search_continues_on_next_page(case: SearchCase, search_results_page: SearchResultsPage) -> None:
    urls = search_results_page.search_items_by_name_under_price(case.query, case.max_price, case.limit)

    search_results_page.verify_page_number(SECOND_PAGE)
    assert len(urls) == case.limit
    assert len(set(urls)) == len(urls), "the same listing was collected twice"


@pytest.mark.parametrize("case", load_search_cases("price_filter"), ids=case_id)
def test_max_price_filter(case: SearchCase, search_results_page: SearchResultsPage) -> None:
    search_results_page.open_results(case.query)
    search_results_page.filter_max_price(case.max_price)
    search_results_page.verify_max_price_filter(case.max_price)


@pytest.mark.parametrize("case", load_search_cases("no_results"), ids=case_id)
def test_search_without_matches_returns_nothing(case: SearchCase, search_results_page: SearchResultsPage) -> None:
    urls = search_results_page.search_items_by_name_under_price(case.query, case.max_price, case.limit)

    search_results_page.verify_no_results_for(case.query)
    assert urls == []
