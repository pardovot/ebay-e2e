# AI test review

The main issue with this test is that it never asserts anything, so it passes even when search is broken. There are a few more problems around it, each one below with a suggested fix.

```python
 1  from playwright.sync_api import sync_playwright
 2  from selenium import webdriver
 3  import time
 4
 5  def test_search_functionality():
 6      browser = sync_playwright().start().chromium.launch()
 7      page = browser.new_page()
 8      page.goto("https://example.com")
 9
10      time.sleep(2)
11
12      search_box = page.locator("#search")
13      search_box.fill("playwright testing")
14
15      page.locator(".button").click()
16
17      time.sleep(3)
18
19      results = page.locator(".result-item")
20
21      browser.close()
```

## 1. No assertion (line 19)

`page.locator(".result-item")` is lazy and doesn't touch the page until something acts or asserts on it, and nothing does here, so the test passes whether search works or not.

```python
expect(results.first).to_be_visible()
expect(results.first).to_contain_text("playwright", ignore_case=True)
```

## 2. No cleanup when something fails (lines 6, 21)

The driver started by `sync_playwright().start()` is never stopped, and `browser.close()` only runs if every line before it passed, so any failure leaves a browser and a driver process running, which adds up quickly on CI.

The simplest fix is the pytest-playwright `page` fixture, which handles launch and teardown:

```python
def test_search_functionality(page: Page):
```

Without the plugin, wrap it in `with sync_playwright() as playwright:` and close the browser in a `finally`.

## 3. Hard sleeps (lines 10, 17)

They add 5 seconds to every run and still might not be enough on a slow agent, while Playwright already waits before `fill` and `click`, and `expect` retries until it passes or times out, so both lines can simply go.

## 4. `.button` is too vague (line 15)

If more than one element has that class, Playwright's strict mode makes `click()` fail, and if only one does, there's no guarantee it's the search button:

```python
page.get_by_role("button", name="Search").click()
```

## 5. Wrong page (lines 8, 12, 13)

example.com has no search box, so `fill` on `#search` waits 30 seconds and times out. The URL should point to the real app and come from config rather than being hardcoded, and a role locator like `get_by_role("searchbox")` holds up better than an id.

## 6. Unused Selenium import (line 2)

It's never used, and if Selenium isn't installed the import fails and pytest can't even load the file, so it should just be removed.

## After the fixes

```python
from playwright.sync_api import Page, expect


def test_search_shows_matching_results(page: Page) -> None:
    page.goto(BASE_URL)
    page.get_by_role("searchbox").fill("playwright testing")
    page.get_by_role("button", name="Search").click()

    results = page.locator(".result-item")
    expect(results.first).to_be_visible()
    expect(results.first).to_contain_text("playwright", ignore_case=True)
```

`BASE_URL` and the locators depend on the real app, and in a real suite they'd sit in a page object instead of inline.
