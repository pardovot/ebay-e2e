from datetime import datetime
from pathlib import Path

import allure
from playwright.sync_api import Page


def capture_screenshot(page: Page, name: str, directory: Path) -> Path:
    """Saves a screenshot under `directory` and attaches it to the Allure report."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{datetime.now():%Y%m%d-%H%M%S}-{name}.png"
    page.screenshot(path=path)
    allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)
    return path
