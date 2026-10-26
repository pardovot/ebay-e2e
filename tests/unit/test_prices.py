from decimal import Decimal

import pytest

from utils.prices import Money, parse_money, parse_price_range


@pytest.mark.parametrize(
    ("label", "low", "high"),
    [
        ("ILS 46.54", Money("ILS", Decimal("46.54")), Money("ILS", Decimal("46.54"))),
        ("ILS 1,234.50", Money("ILS", Decimal("1234.50")), Money("ILS", Decimal("1234.50"))),
        ("US $19.99", Money("USD", Decimal("19.99")), Money("USD", Decimal("19.99"))),
        ("ILS 20.00 to ILS 45.00", Money("ILS", Decimal("20.00")), Money("ILS", Decimal("45.00"))),
        ("ILS 78.20 to ILS 167.62 ILS 86.90", Money("ILS", Decimal("78.20")), Money("ILS", Decimal("167.62"))),
    ],
)
def test_parse_price_range(label: str, low: Money, high: Money) -> None:
    price = parse_price_range(label)

    assert (price.low, price.high) == (low, high)


@pytest.mark.parametrize("label", ["Free shipping", "ILS 20.00 to", "ILS 20.00 to US $45.00"])
def test_parse_price_range_rejects(label: str) -> None:
    with pytest.raises(ValueError):
        parse_price_range(label)


def test_parse_money() -> None:
    assert parse_money("ILS 155.20") == Money("ILS", Decimal("155.20"))


def test_parse_money_rejects_a_range() -> None:
    with pytest.raises(ValueError):
        parse_money("ILS 20.00 to ILS 45.00")
