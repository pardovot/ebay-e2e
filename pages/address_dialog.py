from playwright.sync_api import Locator, Page

from config.settings import Settings
from pages.base_page import BasePage


class AddressDialog(BasePage):
    """The "Are you shipping to <zip>?" prompt eBay opens over item pages, which blocks every click until closed."""

    def __init__(self, page: Page, settings: Settings) -> None:
        super().__init__(page, settings)
        self.dialog = page.locator(".address-dialog__lightbox")

    def dismiss_whenever_shown(self) -> None:
        self.page.add_locator_handler(self.dialog, self._dismiss)

    def _dismiss(self, dialog: Locator) -> None:
        self.page.keyboard.press("Escape")
