import allure
from playwright.sync_api import Page, expect

from config.settings import Settings
from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.sign_in_link = page.locator(".gh-identity").get_by_role("link", name="Sign in", exact=True)

    @allure.step("Log in as a guest")
    def login_as_guest(self) -> None:
        self.visit(self.settings.base_url)
        expect(self.sign_in_link).to_be_visible()
        self.verify_cart_count(0)
