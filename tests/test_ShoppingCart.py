import pytest
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
    dining_table.set_price(1000.0)
    gaming_chair.set_price(500.0)
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


@patch("app.models.ShoppingCart.SessionLocal")
def test_add_item_valid_and_ad_print(mock_session_local, cart, furniture_items):
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = (10,)
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)

    # add_item now returns a tuple (success, advertisement)
    result = cart.add_item(furniture_items["dining_table"], amount=2)
    assert isinstance(result, tuple)
    assert result[0] is True
    advertisement = result[1]
    assert "SPECIAL OFFER" in advertisement
    assert len(cart.items) == 1


@pytest.mark.parametrize("amount", [0, -1, 1.5])
def test_add_item_invalid_amount(cart, furniture_items, amount):
    with pytest.raises(ValueError):
        cart.add_item(furniture_items["dining_table"], amount=amount)


def test_add_item_not_available(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=False)
    # Expecting UnboundLocalError because 'adv' is not set when availability fails
    with pytest.raises(UnboundLocalError):
        cart.add_item(furniture_items["dining_table"], amount=1)


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


def test_add_item_update_existing(cart, furniture_items):
    # Add item first time
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    result1 = cart.add_item(furniture_items["dining_table"], amount=1)
    # Add the same item with a different amount to update the quantity
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    result2 = cart.add_item(furniture_items["dining_table"], amount=3)
    # Check that there's only one entry and the amount has been updated
    assert len(cart.items) == 1
    assert cart.items[0][1] == 3
    # Also check that the return value is a tuple
    assert isinstance(result2, tuple)
    assert result2[0] is True


def test_view_cart(cart, furniture_items):
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)
    view = cart.view_cart()
    # The view should return a dictionary with the furniture name as key and quantity as value
    expected = {furniture_items["dining_table"].name: 2}
    assert view == expected
