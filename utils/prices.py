"""Parses eBay price labels such as "ILS 46.54", "US $19.99" or "ILS 20.00 to ILS 45.00"."""
import re
from dataclasses import dataclass
from decimal import Decimal

# One price: a currency prefix ("US $", "$" or a three letter code), then an amount with optional
# thousands commas. Groups: currency, amount.
PRICE_PATTERN = re.compile(r"(?P<currency>US \$|\$|[A-Z]{3})\s?(?P<amount>\d[\d,]*(?:\.\d+)?)")
# The joiner between the two ends of a variation price range.
RANGE_SEPARATOR_PATTERN = re.compile(r"\s+to\b\s*")
DOLLAR_PREFIXES = {"$", "US $"}


@dataclass(frozen=True)
class Money:
    currency: str
    amount: Decimal

    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"


@dataclass(frozen=True)
class PriceRange:
    low: Money
    high: Money


def _money(match: re.Match[str]) -> Money:
    currency = "USD" if match["currency"] in DOLLAR_PREFIXES else match["currency"]
    return Money(currency, Decimal(match["amount"].replace(",", "")))


def parse_price_range(label: str) -> PriceRange:
    """The leading price or "X to Y" range of a label, ignoring whatever follows it."""
    text = label.strip()
    first = PRICE_PATTERN.match(text)
    if first is None:
        raise ValueError(f"Not a price label: {label!r}")
    low = _money(first)
    separator = RANGE_SEPARATOR_PATTERN.match(text, first.end())
    if separator is None:
        return PriceRange(low, low)
    second = PRICE_PATTERN.match(text, separator.end())
    if second is None:
        raise ValueError(f"Price range without an upper bound: {label!r}")
    high = _money(second)
    if high.currency != low.currency:
        raise ValueError(f"Price range mixes currencies: {label!r}")
    return PriceRange(low, high)


def parse_money(label: str) -> Money:
    """Parses a label that holds exactly one price."""
    match = PRICE_PATTERN.fullmatch(label.strip())
    if match is None:
        raise ValueError(f"Not a single price: {label!r}")
    return _money(match)
