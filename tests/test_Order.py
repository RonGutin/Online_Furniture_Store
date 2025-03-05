import pytest
from app.models.EnumsClass import OrderStatus
from app.models.ShoppingCart import ShoppingCart
from app.models.order import Order
from app import utils


class DummyQuery:
    def __init__(self):
        self.updated = False

    def filter(self, *args, **kwargs):
        return self

    def update(self, values):
        self.updated = True
        return 1


class DummySession:
    def __init__(self):
        self.added_objects = []
        self.committed = False

    def add(self, obj):
        self.added_objects.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        obj.id = 1

    def query(self, model):
        return DummyQuery()

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def patch_session_local(monkeypatch):
    def _dummy_session_local():
        return DummySession()

    monkeypatch.setattr("app.models.order.SessionLocal", _dummy_session_local)


@pytest.fixture(autouse=True)
def patch_inventory(monkeypatch):
    monkeypatch.setattr(utils, "get_index_furniture_by_values", lambda item: 10)


class DummyFurniture:
    def __init__(self, price):
        self._price = price
        self.color = "red"
        self.dimensions = (100, 50, 30)
        self.material = "wood"

    def get_price(self):
        return self._price

    def calculate_discount(self, discount):
        if discount < 0 or discount > 100:
            raise ValueError("Invalid discount")
        return self._price * (1 - discount / 100)

    def check_availability(self, amount):
        return True

    def Print_matching_product_advertisement(self):
        print("*** SPECIAL OFFER !!! ***\nSome advertisement text")


@pytest.fixture
def dummy_cart():
    cart = ShoppingCart()
    dummy_furniture = DummyFurniture(1000)
    cart.items = [(dummy_furniture, 2)]
    cart.get_total_price = lambda: sum(f.get_price() * amt for f, amt in cart.items)
    return cart


def test_order_creation(dummy_cart):
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
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    initial_status = order.get_status()
    order.update_status()
    expected_status = OrderStatus[initial_status].value + 1
    assert order.get_status() == OrderStatus(expected_status).name


def test_update_status_already_delivered(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    order.set_status(OrderStatus.DELIVERED.value)
    with pytest.raises(ValueError) as exc_info:
        order.update_status()
    assert "Order is already in final status (DELIVERED)" in str(exc_info.value)


def test_get_status(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    expected_status_name = OrderStatus(order._status).name
    assert order.get_status() == expected_status_name


def test_order_repr(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    rep = repr(order)
    assert rep.startswith("Order(id = ")
    assert "User email = test@example.com" in rep
    assert "Total price = 2000.00$" in rep
    assert f"Status = {OrderStatus(order._status).name}" in rep


def test_invalid_user_mail_type(dummy_cart):
    with pytest.raises(TypeError, match="user_mail must be a string."):
        Order(user_mail=123, cart=dummy_cart, coupon_id=42)


def test_invalid_cart_type():
    with pytest.raises(TypeError, match="cart must be an instance of ShoppingCart."):
        Order(user_mail="test@example.com", cart="not a cart", coupon_id=42)


def test_invalid_coupon_type(dummy_cart):
    with pytest.raises(TypeError, match="coupon_id must be an integer or None."):
        Order(user_mail="test@example.com", cart=dummy_cart, coupon_id="invalid")


def test_set_user_mail_invalid(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="user_mail must be a string."):
        order.set_user_mail(123)


def test_set_total_price_invalid(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="total_price must be a number."):
        order.set_total_price("not a number")


def test_set_status_invalid_type(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="status must be a int."):
        order.set_status("invalid")


def test_set_status_invalid_value(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(ValueError, match="Invalid status value."):
        order.set_status(999)


def test_set_items_invalid(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="items must be a list."):
        order.set_items("not a list")


def test_set_coupon_id_invalid(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="coupon_id must be an integer or None."):
        order.set_coupon_id("invalid")


def test_set_id_invalid(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    with pytest.raises(TypeError, match="order_id must be an integer or None."):
        order.set_id("not an int")
