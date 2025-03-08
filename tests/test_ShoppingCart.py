import pytest
from unittest.mock import patch, MagicMock
from app.models.ShoppingCart import ShoppingCart
from app.models.FurnituresClass import DiningTable, GamingChair


@pytest.fixture
def cart():
    """
    Fixture that provides a fresh ShoppingCart instance for testing.

    Returns:
        ShoppingCart: An empty shopping cart instance.
    """
    return ShoppingCart()


@pytest.fixture
def furniture_items():
    """
    Fixture that provides furniture items for testing.

    Creates and configures a dining table and gaming chair with
    predefined properties and prices.

    Returns:
        dict: A dictionary containing the furniture items with keys
              'dining_table' and 'gaming_chair'.
    """
    dining_table = DiningTable(color="brown", material="wood")
    gaming_chair = GamingChair(color="Black", is_adjustable=True, has_armrest=True)
    dining_table.set_price(1000.0)
    gaming_chair.set_price(500.0)
    return {"dining_table": dining_table, "gaming_chair": gaming_chair}


def test_get_total_price_empty_cart(cart):
    """
    Test get_total_price method on an empty cart.

    Verifies that the total price of an empty cart is 0.

    Args:
        cart: The shopping cart fixture.
    """
    assert cart.get_total_price() == 0


def test_get_total_price_with_items(cart, furniture_items):
    """
    Test get_total_price method with items in the cart.

    Verifies that the total price is calculated correctly as the sum of
    price * quantity for each item in the cart.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    furniture_items["gaming_chair"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)
    cart.add_item(furniture_items["gaming_chair"], amount=1)
    assert cart.get_total_price() == 2 * 1000 + 1 * 500


@patch("app.models.ShoppingCart.SessionLocal")
def test_get_coupon_discount_and_id_valid(mock_session_local, cart):
    """
    Test get_coupon_discount_and_id with a valid coupon code.

    Verifies that the method returns the correct discount percentage and
    coupon ID when a valid coupon code is provided.

    Args:
        mock_session_local: Mock for the SessionLocal database session.
        cart: The shopping cart fixture.
    """
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
    """
    Test get_coupon_discount_and_id with an invalid coupon code.

    Verifies that the method returns a discount of 0 and None for coupon ID
    when an invalid coupon code is provided.

    Args:
        mock_session_local: Mock for the SessionLocal database session.
        cart: The shopping cart fixture.
    """
    mock_session = MagicMock()
    mock_session_local.return_value = mock_session
    mock_query = MagicMock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None
    discount, coupon_id = cart.get_coupon_discount_and_id("FAKECODE")
    assert discount == 0
    assert coupon_id is None


def test_get_coupon_discount_and_id_non_string(cart):
    """
    Test get_coupon_discount_and_id with a non-string coupon code.

    Verifies that the method raises a TypeError when the coupon code is not a string.

    Args:
        cart: The shopping cart fixture.
    """
    with pytest.raises(TypeError, match="Coupon code must be a string"):
        cart.get_coupon_discount_and_id(123)


def test_apply_discount_empty_cart(cart):
    """
    Test apply_discount on an empty cart.

    Verifies that applying a discount to an empty cart results in a total price of 0.

    Args:
        cart: The shopping cart fixture.
    """
    assert cart.apply_discount(10) == 0


def test_apply_discount_with_items(cart, furniture_items):
    """
    Test apply_discount with items in the cart.

    Verifies that the discount is correctly applied to the total price.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)
    assert cart.apply_discount(10) == 1800.0


def test_apply_discount_non_int(cart):
    """
    Test apply_discount with a non-integer discount percentage.

    Verifies that the method raises a TypeError when the discount percentage is not an integer.

    Args:
        cart: The shopping cart fixture.
    """
    with pytest.raises(TypeError, match="Discount percentage must be an integer"):
        cart.apply_discount(10.5)


@patch("app.models.ShoppingCart.SessionLocal")
def test_add_item_valid_and_ad_print(mock_session_local, cart, furniture_items):
    """
    Test add_item with a valid item and verify advertisement is returned.

    Verifies that the item is added to the cart successfully and that the method
    returns True and an advertisement string.

    Args:
        mock_session_local: Mock for the SessionLocal database session.
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_db.query.return_value.filter.return_value.first.return_value = (10,)
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    with patch.object(
        furniture_items["dining_table"],
        "Print_matching_product_advertisement",
        return_value="*** SPECIAL OFFER ***",
    ):
        result = cart.add_item(furniture_items["dining_table"], amount=2)
    assert isinstance(result, tuple)
    assert result[0] is True
    advertisement = result[1]
    assert "SPECIAL OFFER" in advertisement
    assert len(cart.items) == 1


def test_add_item_not_available(cart, furniture_items):
    """
    Test add_item when the item is not available.

    Verifies that the method returns False and an empty string when
    the item is not available.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=False)
    result = cart.add_item(furniture_items["dining_table"], amount=1)
    assert result == (False, "")


def test_add_item_invalid_amount(cart, furniture_items):
    """
    Test add_item with invalid amount values.

    Verifies that the method raises ValueError for zero or negative amounts and
    TypeError for non-integer amounts.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    with pytest.raises(ValueError, match="Not the right amount"):
        cart.add_item(furniture_items["dining_table"], amount=0)
    with pytest.raises(ValueError, match="Amount must be an integer"):
        cart.add_item(furniture_items["dining_table"], amount="two")


def test_add_item_invalid_furniture(cart):
    """
    Test add_item with an invalid furniture item.

    Verifies that the method raises TypeError when the item is not a furniture instance.

    Args:
        cart: The shopping cart fixture.
    """
    with pytest.raises(
        TypeError, match="Furniture must be an instance of Furniture class"
    ):
        cart.add_item("not a furniture", amount=1)


def test_remove_item_valid(cart, furniture_items):
    """
    Test remove_item with a valid item in the cart.

    Verifies that the item is successfully removed from the cart.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=1)
    cart.remove_item(furniture_items["dining_table"])
    assert len(cart.items) == 0


def test_remove_item_not_in_cart(cart, furniture_items):
    """
    Test remove_item with an item not in the cart.

    Verifies that the method raises ValueError when attempting to remove
    an item that is not in the cart.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    with pytest.raises(ValueError, match="Item not in cart - nothing to remove"):
        cart.remove_item(furniture_items["gaming_chair"])


def test_repr_empty_cart(cart):
    """
    Test the __repr__ method on an empty cart.

    Verifies that the string representation of an empty cart is "Shopping cart is empty."

    Args:
        cart: The shopping cart fixture.
    """
    assert repr(cart) == "Shopping cart is empty."


def test_repr_non_empty_cart(cart, furniture_items):
    """
    Test the __repr__ method on a non-empty cart.

    Verifies that the string representation of a non-empty cart includes
    item details and the "Shopping Cart:" heading.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=1)
    cart_repr = repr(cart)
    assert "Shopping Cart:" in cart_repr
    assert "Table Details:" in cart_repr


def test_add_item_update_existing(cart, furniture_items):
    """
    Test add_item updating an existing item in the cart.

    Verifies that adding an item that's already in the cart updates its quantity
    instead of adding a duplicate entry.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    result2 = cart.add_item(furniture_items["dining_table"], amount=3)
    assert len(cart.items) == 1
    assert cart.items[0][1] == 3
    assert isinstance(result2, tuple)
    assert result2[0] is True


def test_view_cart(cart, furniture_items):
    """
    Test the view_cart method with items in the cart.

    Verifies that view_cart returns a dictionary with item names as keys
    and quantities as values.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)
    view = cart.view_cart()
    expected = {furniture_items["dining_table"].name: 2}
    assert view == expected


def test_view_cart_empty(cart):
    """
    Test viewing an empty cart.

    Verifies that view_cart returns an empty dictionary when the cart is empty.

    Args:
        cart: The shopping cart fixture.
    """
    view = cart.view_cart()
    assert view == {}


def test_view_cart_multiple_items(cart, furniture_items):
    """
    Test viewing a cart with multiple items.

    Verifies that view_cart returns a dictionary with all items correctly
    represented with their names and quantities.

    Args:
        cart: The shopping cart fixture.
        furniture_items: The furniture items fixture.
    """
    furniture_items["dining_table"].check_availability = MagicMock(return_value=True)
    furniture_items["gaming_chair"].check_availability = MagicMock(return_value=True)
    cart.add_item(furniture_items["dining_table"], amount=2)
    cart.add_item(furniture_items["gaming_chair"], amount=1)

    view = cart.view_cart()
    assert furniture_items["dining_table"].name in view
    assert furniture_items["gaming_chair"].name in view
    assert view[furniture_items["gaming_chair"].name] == 1
