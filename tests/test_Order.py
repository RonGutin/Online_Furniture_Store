import pytest
from unittest.mock import MagicMock
from app.models.EnumsClass import OrderStatus
from app.models.ShoppingCart import ShoppingCart
from app.models.order import Order
from app import utils


class DummyQuery:
    """
    Mock implementation of a database query for testing.

    Provides minimal implementation of filter and update methods
    to simulate database queries without actual database connections.

    Attributes:
        updated (bool): Flag to track if update was called
    """

    def __init__(self):
        self.updated = False

    def filter(self, *args, **kwargs):
        """
        Mock filter method that returns self for method chaining.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            DummyQuery: Returns self for method chaining
        """
        return self

    def update(self, values):
        """
        Mock update method that sets updated flag and returns 1.

        Args:
            values: The values to update (unused)

        Returns:
            int: Always returns 1 to simulate one row updated
        """
        self.updated = True
        return 1


class DummySession:
    """
    Mock implementation of a database session for testing.

    Provides minimal implementation of database session methods
    to test Order functionality without actual database connections.

    Attributes:
        added_objects (list): List of objects added to the session
        committed (bool): Flag to track if commit was called
    """

    def __init__(self):
        self.added_objects = []
        self.committed = False

    def add(self, obj):
        """
        Mock add method that stores objects in the added_objects list.

        Args:
            obj: The object to add to the session
        """
        self.added_objects.append(obj)

    def commit(self):
        """
        Mock commit method that sets the committed flag.
        """
        self.committed = True

    def refresh(self, obj):
        """
        Mock refresh method that sets the id attribute of the object to 1.

        Args:
            obj: The object to refresh
        """
        obj.id = 1

    def query(self, model):
        """
        Mock query method that returns a DummyQuery instance.

        Args:
            model: The model to query (unused)

        Returns:
            DummyQuery: A new instance of DummyQuery
        """
        return DummyQuery()

    def rollback(self):
        """
        Mock rollback method.
        """
        pass

    def close(self):
        """
        Mock close method.
        """
        pass


@pytest.fixture(autouse=True)
def patch_session_local(monkeypatch):
    """
    Fixture to replace SessionLocal with a function returning DummySession.

    This fixture is automatically applied to all tests in this module.
    It replaces the real database session with a dummy implementation.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """

    def _dummy_session_local():
        return DummySession()

    monkeypatch.setattr("app.models.order.SessionLocal", _dummy_session_local)


@pytest.fixture(autouse=True)
def patch_inventory(monkeypatch):
    """
    Fixture to replace the get_index_furniture_by_values function.

    This fixture is automatically applied to all tests in this module.
    It replaces the get_index_furniture_by_values function to always return 10.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    monkeypatch.setattr(utils, "get_index_furniture_by_values", lambda item: 10)


class DummyFurniture:
    """
    Mock implementation of a furniture item for testing.

    Provides the minimal interface needed to test Order functionality.

    Attributes:
        _price (float): The price of the furniture
        color (str): The color of the furniture
        dimensions (tuple): The dimensions of the furniture
        material (str): The material of the furniture
    """

    def __init__(self, price):
        self._price = price
        self.color = "red"
        self.dimensions = (100, 50, 30)
        self.material = "wood"

    def get_price(self):
        """
        Get the price of the furniture.

        Returns:
            float: The price of the furniture
        """
        return self._price

    def calculate_discount(self, discount):
        """
        Calculate the discounted price.

        Args:
            discount (float): The discount percentage (0-100)

        Returns:
            float: The discounted price

        Raises:
            ValueError: If discount is less than 0 or greater than 100
        """
        if discount < 0 or discount > 100:
            raise ValueError("Invalid discount")
        return self._price * (1 - discount / 100)

    def check_availability(self, amount):
        """
        Check if the furniture is available in the specified amount.

        For testing purposes, this always returns True.

        Args:
            amount (int): The amount to check

        Returns:
            bool: Always returns True for testing
        """
        return True

    def Print_matching_product_advertisement(self):
        """
        Print an advertisement for matching products.

        This is a simplified version for testing.
        """
        print("*** SPECIAL OFFER !!! ***\nSome advertisement text")


@pytest.fixture
def dummy_cart():
    """
    Fixture that provides a ShoppingCart with a DummyFurniture item.

    Returns:
        ShoppingCart: A shopping cart with one DummyFurniture item
    """
    cart = ShoppingCart()
    dummy_furniture = DummyFurniture(1000)
    cart.items = [(dummy_furniture, 2)]
    cart.get_total_price = lambda: sum(f.get_price() * amt for f, amt in cart.items)
    return cart


def test_order_creation(dummy_cart):
    """
    Test the creation of an Order with valid parameters.

    Verifies that the Order is correctly initialized with the provided parameters
    and that all getters return the expected values.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    assert order.get_user_mail() == "test@example.com"
    assert order.get_total_price() == 2000
    assert order.get_coupon_id() == 42
    assert order.get_status() == OrderStatus.PENDING.name
    assert order.get_id() == 1
    assert isinstance(order.get_items(), list)
    for item, amount in order.get_items():
        assert amount == 2


def test_update_status(dummy_cart):
    """
    Test the update_status method.

    Verifies that calling update_status increments the order status correctly.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    initial_status = order.get_status()
    order.update_status()
    expected_status = OrderStatus[initial_status].value + 1
    assert order.get_status() == OrderStatus(expected_status).name


def test_update_status_already_delivered(dummy_cart):
    """
    Test update_status when the order is already delivered.

    Verifies that attempting to update the status of an already delivered order
    raises a ValueError with the expected message.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    order.set_status(OrderStatus.DELIVERED.value)
    with pytest.raises(ValueError) as exc_info:
        order.update_status()
    assert "Order is already in final status (DELIVERED)" in str(exc_info.value)


def test_get_status(dummy_cart):
    """
    Test the get_status method.

    Verifies that get_status returns the correct status name.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    expected_status_name = OrderStatus(order._status).name
    assert order.get_status() == expected_status_name


def test_order_repr(dummy_cart):
    """
    Test the __repr__ method of Order.

    Verifies that the string representation of an Order contains the expected information.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    rep = repr(order)
    assert rep.startswith("Order(id = ")
    assert "User email = test@example.com" in rep
    assert "Total price = 2000.00$" in rep
    assert f"Status = {OrderStatus(order._status).name}" in rep


def test_invalid_user_mail_type(dummy_cart):
    """
    Test Order creation with an invalid user_mail type.

    Verifies that creating an Order with a non-string user_mail raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    with pytest.raises(TypeError, match="user_mail must be a string."):
        Order(user_mail=123, cart=dummy_cart, coupon_id=42)


def test_invalid_cart_type():
    """
    Test Order creation with an invalid cart type.

    Verifies that creating an Order with a non-ShoppingCart cart raises a TypeError.
    """
    with pytest.raises(TypeError, match="cart must be an instance of ShoppingCart."):
        Order(user_mail="test@example.com", cart="not a cart", coupon_id=42)


def test_invalid_coupon_type(dummy_cart):
    """
    Test Order creation with an invalid coupon_id type.

    Verifies that creating an Order with a non-integer coupon_id raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    with pytest.raises(TypeError, match="coupon_id must be an integer or None."):
        Order(user_mail="test@example.com", cart=dummy_cart, coupon_id="invalid")


def test_set_user_mail_invalid(dummy_cart):
    """
    Test set_user_mail with an invalid type.

    Verifies that calling set_user_mail with a non-string raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="user_mail must be a string."):
        order.set_user_mail(123)


def test_set_total_price_invalid(dummy_cart):
    """
    Test set_total_price with an invalid type.

    Verifies that calling set_total_price with a non-number raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="total_price must be a number."):
        order.set_total_price("not a number")


def test_set_status_invalid_type(dummy_cart):
    """
    Test set_status with an invalid type.

    Verifies that calling set_status with a non-int raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="status must be a int."):
        order.set_status("invalid")


def test_set_status_invalid_value(dummy_cart):
    """
    Test set_status with an invalid value.

    Verifies that calling set_status with a value not in OrderStatus raises a ValueError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(ValueError, match="Invalid status value."):
        order.set_status(999)


def test_set_items_invalid(dummy_cart):
    """
    Test set_items with an invalid type.

    Verifies that calling set_items with a non-list raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="items must be a list."):
        order.set_items("not a list")


def test_set_coupon_id_invalid(dummy_cart):
    """
    Test set_coupon_id with an invalid type.

    Verifies that calling set_coupon_id with a non-integer raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="coupon_id must be an integer or None."):
        order.set_coupon_id("invalid")


def test_set_id_invalid(dummy_cart):
    """
    Test set_id with an invalid type.

    Verifies that calling set_id with a non-integer raises a TypeError.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="order_id must be an integer or None."):
        order.set_id("not an int")


def test_setters_successful(dummy_cart):
    """
    Test all setter methods with valid values.

    Verifies that all setter methods correctly update their respective attributes.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)

    # Test set_user_mail success case (line 38)
    order.set_user_mail("new@example.com")
    assert order.get_user_mail() == "new@example.com"

    # Test set_total_price success case (line 46)
    order.set_total_price(3000.50)
    assert order.get_total_price() == 3000.50

    # Test set_items success case (line 64)
    dummy_furniture = dummy_cart.items[0][0]
    new_items = [(dummy_furniture, 3)]
    order.set_items(new_items)
    assert order.get_items() == new_items

    # Test set_coupon_id success case (line 72)
    order.set_coupon_id(99)
    assert order.get_coupon_id() == 99

    # Test set_id success case (line 80)
    order.set_id(123)
    assert order.get_id() == 123

    # Test set_coupon_id with None (line 72)
    order.set_coupon_id(None)
    assert order.get_coupon_id() is None

    # Test set_id with None (line 80)
    order.set_id(None)
    assert order.get_id() is None


def test_save_to_db_exception(dummy_cart, monkeypatch):
    """
    Test exception handling in _save_to_db method.

    Verifies that exceptions in the database operation are properly caught and re-raised.

    Args:
        dummy_cart: The dummy_cart fixture
        monkeypatch: Pytest's monkeypatch fixture
    """
    # Create a mock session that raises an exception
    mock_session = MagicMock()
    mock_session.add.side_effect = Exception("Database error")

    # Mock the SessionLocal to return our mock session
    monkeypatch.setattr("app.models.order.SessionLocal", lambda: mock_session)

    # Test that the exception in _save_to_db is properly caught and re-raised
    with pytest.raises(
        Exception, match="Error saving order to database: Database error"
    ):
        Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)


def test_update_status_exception(dummy_cart, monkeypatch):
    """
    Test exception handling in update_status method.

    Verifies that exceptions in the database operation are properly caught and re-raised.

    Args:
        dummy_cart: The dummy_cart fixture
        monkeypatch: Pytest's monkeypatch fixture
    """
    # First create an order with the normal mock
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)

    # Create a mock session that raises an exception during update
    mock_session = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    filter_mock.update.side_effect = Exception("Database error during update")
    query_mock.filter.return_value = filter_mock
    mock_session.query.return_value = query_mock

    # Mock the SessionLocal to return our mock session
    monkeypatch.setattr("app.models.order.SessionLocal", lambda: mock_session)

    # Test that the exception in update_status is properly caught and re-raised
    with pytest.raises(
        Exception, match="Error updating order status: Database error during update"
    ):
        order.update_status()


def test_set_status_with_enum_value(dummy_cart):
    """
    Test set_status with various OrderStatus enum values.

    Verifies that set_status correctly updates the status when using enum values.

    Args:
        dummy_cart: The dummy_cart fixture
    """
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)

    # Test setting status to PROCESSING (value 1)
    order.set_status(OrderStatus.PENDING.value)
    assert order.get_status() == "PENDING"

    # Test setting status to SHIPPED (value 2)
    order.set_status(OrderStatus.SHIPPED.value)
    assert order.get_status() == "SHIPPED"

    # Test setting status to DELIVERED (value 3)
    order.set_status(OrderStatus.DELIVERED.value)
    assert order.get_status() == "DELIVERED"
