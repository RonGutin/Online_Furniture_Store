import pytest
import io
from unittest.mock import patch, MagicMock
from app.models.ShoppingCart import ShoppingCart
from app.models.FurnituresClass import DiningTable, GamingChair


@pytest.fixture
def cart():
    return ShoppingCart()


@pytest.fixture
def furniture_items():
    dining_table = DiningTable(color="brown", material="wood")
    gaming_chair = GamingChair(color="Black", is_adjustable=True, has_armrest=True)
    dining_table.price = 1000.0
    gaming_chair.price = 500.0
    return {"dining_table": dining_table, "gaming_chair": gaming_chair}


def test_get_total_price_empty_cart(cart):
    assert cart.get_total_price() == 0


def test_get_total_price_with_items(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    furniture_items["gaming_chair"].check_availability = MagicMock(return_value=True)

    cart.add_item(furniture_items["dining_table"], amount=2)
    cart.add_item(furniture_items["gaming_chair"], amount=1)

    assert cart.get_total_price() == 2 * 1000 + 1 * 500


@patch("app.models.ShoppingCart.SessionLocal")
def test_get_coupon_discount_and_id_valid(mock_session_local, cart):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query

    mock_coupon = MagicMock()
    mock_coupon.CouponValue = "SAVE10"
    mock_coupon.Discount = 10
    mock_coupon.idCouponsCodes = 1
    mock_query.filter.return_value.first.return_value = mock_coupon

    discount, coupon_id = cart.get_coupon_discount_and_id("SAVE10")

    assert discount == 10
    assert coupon_id == 1


@patch("app.models.ShoppingCart.SessionLocal")
def test_get_coupon_discount_and_id_invalid(mock_session_local, cart):
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None

    discount, coupon_id = cart.get_coupon_discount_and_id("FAKECODE")

    assert discount == 0
    assert coupon_id is None


def test_apply_discount_empty_cart(cart):
    assert cart.apply_discount(10) == 0


def test_apply_discount_with_items(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)

    assert cart.apply_discount(10) == 1800.0


@patch("sys.stdout", new_callable=io.StringIO)
@patch("app.models.ShoppingCart.SessionLocal")
@patch.object(
    DiningTable,
    "get_match_furniture",
    return_value="*** SPECIAL OFFER ***\nWe found a matching chair!",
)
def test_add_item_valid_and_ad_print(
    mock_get_match_furniture, mock_session, mock_stdout, cart, furniture_items
):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = (
        10,
    )  # מסמל שיש כמות במלאי

    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)

    result = cart.add_item(furniture_items["dining_table"], amount=2)

    assert result is True
    assert len(cart.items) == 1

    printed_output = mock_stdout.getvalue()
    assert (
        "SPECIAL OFFER" in printed_output
    ), f"Expected 'SPECIAL OFFER' in output, but got:\n{printed_output}"


@pytest.mark.parametrize("amount", [0, -1, 1.5])
def test_add_item_invalid_amount(cart, furniture_items, amount):
    with pytest.raises(ValueError):
        cart.add_item(furniture_items["dining_table"], amount=amount)


def test_add_item_not_available(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=False)

    result = cart.add_item(furniture_items["dining_table"], amount=1)

    assert result is False
    assert len(cart.items) == 0


def test_remove_item_valid(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=1)

    cart.remove_item(furniture_items["dining_table"])

    assert len(cart.items) == 0


def test_remove_item_not_in_cart(cart, furniture_items):
    with pytest.raises(ValueError):
        cart.remove_item(furniture_items["gaming_chair"])


def test_repr_empty_cart(cart):
    assert repr(cart) == "Shopping cart is empty."


def test_repr_non_empty_cart(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=1)

    cart_repr = repr(cart)

    assert "Shopping Cart:" in cart_repr
    assert "Table Details:" in cart_repr
