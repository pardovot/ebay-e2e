from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Run settings, each one overridable by an EBAY_<NAME> environment variable."""

    model_config = SettingsConfigDict(env_prefix="EBAY_")

    base_url: str = "https://www.ebay.com"
    cart_url: str = "https://cart.ebay.com"
    currency: str = "ILS"
    headless: bool = False
    slow_mo_ms: int = Field(default=0, ge=0)
    max_result_pages: int = Field(default=5, ge=1)
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"
