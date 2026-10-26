import json
from decimal import Decimal

from pydantic import BaseModel, Field

from config.settings import PROJECT_ROOT

SEARCH_CASES_PATH = PROJECT_ROOT / "data" / "search_cases.json"


class SearchCase(BaseModel):
    id: str
    query: str = Field(min_length=1)
    max_price: Decimal = Field(gt=0)
    # The same default as search_items_by_name_under_price().
    limit: int = Field(default=5, ge=0)


def load_search_cases(group: str) -> list[SearchCase]:
    groups = json.loads(SEARCH_CASES_PATH.read_text(encoding="utf-8"))
    return [SearchCase.model_validate(case) for case in groups[group]]
