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
    """
    מחליף את SessionLocal כך שיחזיר DummySession
    במקום אובייקט Session אמיתי.
    """

    def _dummy_session_local():
        return DummySession()

    monkeypatch.setattr("app.models.order.SessionLocal", _dummy_session_local)


@pytest.fixture(autouse=True)
def patch_inventory(monkeypatch):
    # Patch לפונקציה get_index_furniture_by_values מהמודול utils
    monkeypatch.setattr(utils, "get_index_furniture_by_values", lambda self, item: 10)


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
    cart.items = {dummy_furniture: 2}
    cart.get_total_price = lambda: sum(
        f.get_price() * amt for f, amt in cart.items.items()
    )
    return cart


def test_order_creation(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    assert order.user_mail == "test@example.com"
    assert order.total_price == 2000
    assert order.coupon_id == 42
    assert order.status == OrderStatus.PENDING.value
    assert order.id == 1
    assert isinstance(order.items, dict)
    for item, amount in order.items.items():
        assert amount == 2


def test_update_status(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    initial_status = order.status
    order.update_status()
    expected_status = OrderStatus(initial_status + 1).value
    assert order.status == expected_status


def test_update_status_already_delivered(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    order.status = OrderStatus.DELIVERED.value
    with pytest.raises(ValueError) as exc_info:
        order.update_status()
    assert "Order is already in final status (DELIVERED)" in str(exc_info.value)


def test_get_status(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    expected_status_name = OrderStatus(order.status).name
    assert order.get_status() == expected_status_name


def test_order_repr(dummy_cart):
    order = Order(user_mail="test@example.com", cart=dummy_cart, coupon_id=42)
    rep = repr(order)
    assert "Order(id = 1" in rep
    assert "User email = test@example.com" in rep
    assert "Total price = 2000.00$" in rep
    assert f"Status = {OrderStatus(order.status).name}" in rep
