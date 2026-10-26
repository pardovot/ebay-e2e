import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = PROJECT_ROOT / "config" / "profiles"


def profile_path() -> Path | None:
    """The YAML file of the profile named by EBAY_PROFILE, or None when it's unset."""
    profile = os.environ.get("EBAY_PROFILE")
    if profile is None:
        return None
    path = PROFILES_DIR / f"{profile}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown profile '{profile}', expected {path}")
    return path


class Settings(BaseSettings):
    """Run settings. EBAY_<NAME> environment variables win over the EBAY_PROFILE profile, which wins over these."""

    model_config = SettingsConfigDict(env_prefix="EBAY_", extra="forbid")

    base_url: str = "https://www.ebay.com"
    cart_url: str = "https://cart.ebay.com"
    currency: str = "ILS"
    headless: bool = False
    slow_mo_ms: int = Field(default=0, ge=0)
    max_result_pages: int = Field(default=5, ge=1)
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return init_settings, env_settings, YamlConfigSettingsSource(settings_cls, yaml_file=profile_path())
