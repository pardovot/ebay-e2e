# eBay e2e

Playwright + pytest tests for an eBay guest shopping flow: search items under a price, add them to the cart with random variants, and check the cart total against a budget.

## Setup

Needs Python 3.11+, and Node.js for the Allure report.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
playwright install chromium
```

## Run

```bash
pytest tests/unit                   # offline
pytest -m e2e -n 2                  # live ebay.com
EBAY_PROFILE=debug pytest -m e2e    # slowed down to watch
```

Settings have defaults in `config/settings.py`. `EBAY_PROFILE` picks a profile from `config/profiles/` (`debug`, `us` for USD prices), and `EBAY_<NAME>` environment variables override both, e.g. `EBAY_CURRENCY=EUR`.

## Test data

`data/search_cases.json` holds the search cases, grouped by test, and each case runs as its own test:

```json
{ "id": "shoes-under-220", "query": "shoes", "max_price": 220, "limit": 2 }
```

## Tests

| File | Covers |
| --- | --- |
| `test_journey.py` | the full scenario: guest, search under a price, add the items, check the cart total |
| `test_search.py` | result limit, paging, the price filter, no results |
| `test_item.py` | random variants, Add to cart without choosing variants |
| `test_cart.py` | a total over budget fails the check |

Each test runs in a new guest session. Item and cart tests take their items from one shared search, the `listings` fixture.

## Reports

The report of the latest run is at https://pardovot.github.io/ebay-e2e/, with its [JUnit XML](https://pardovot.github.io/ebay-e2e/junit.xml). To build one from a local run:

```bash
npx allure@3.22.1 generate ./allure-results --clean --open
```

The Allure report has a step for every page action, screenshots of each added item and the cart, and a video and trace of every failed test. JUnit XML goes to `reports/`, and screenshots, videos and traces to `artifacts/`.

## Structure

```
config/              settings and profiles
data/                test data
pages/               page objects, BasePage holds navigation and the header
utils/               price parsing, item URLs, test data loader, screenshots, ad hosts
tests/e2e/           live tests, fixtures in conftest.py
tests/unit/          price parsing tests
```

- Tests only call page object methods, locators stay in the pages.
- Every page action and check is an Allure step.
- No fixed sleeps. After each navigation the pages wait for eBay's scripts, since input before they run is lost.
- The "Are you shipping to...?" popup is closed by `page.add_locator_handler`.

## Limitations

- Guest only, since no test account was provided.
- Prices are compared in the currency eBay shows for the runner's location, ILS from Israel. A mismatch fails the run.
- The budget is checked against the cart's items total, because eBay's subtotal includes shipping.
- A price range counts by its top price, so any random variant stays within budget.
- Only Buy It Now listings are used, since auctions have no Add to cart.
- Quantity stays 1, since the budget is per item times the item count.
- Search stops after 5 result pages (`EBAY_MAX_RESULT_PAGES`), so a rare item can't page through all of eBay.
- eBay blocks headless browsers, so the tests run headed.
- eBay also blocks automated sessions after a few runs close together, and the test then fails with "eBay served its bot wall".
- eBay blocks GitHub hosted runners on the first page, so there's no CI.
- Ad and tracking hosts are blocked in the test browser to speed up page loads.

## AI test review

See [ReadMeAIBugs.md](ReadMeAIBugs.md).
