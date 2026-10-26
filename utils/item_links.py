import re

# The numeric listing id in an item link, e.g. "/itm/376322399945?_skw=shoes&hash=..." -> "376322399945".
ITEM_ID_PATTERN = re.compile(r"/itm/(\d+)")


def item_id(href: str) -> str:
    match = ITEM_ID_PATTERN.search(href)
    if match is None:
        raise ValueError(f"Not an item link: {href!r}")
    return match[1]


def canonical_item_url(href: str, base_url: str) -> str:
    """Item link without search tracking parameters, so the same listing always maps to one URL."""
    return f"{base_url}/itm/{item_id(href)}"
