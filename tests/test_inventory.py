import pytest
from flask import Flask, Response
from unittest.mock import MagicMock
from app.models.inventory import Inventory


class DummyItem:
    pass


class DummyInventoryDB:
    def __init__(self, quantity, price=100):
        self.quantity = quantity
        self.price = price

    def to_dict(self):
        return {"quantity": self.quantity, "price": self.price}


@pytest.fixture(autouse=True)
def reset_inventory_singleton():
    Inventory._instance = None


@pytest.fixture
def inv():
    return Inventory()


def test_update_amount_in_inventory_valid(monkeypatch, inv):
    monkeypatch.setattr(
        "app.models.inventory.transform_pascal_to_snake", lambda x: "dummy_item"
    )
    monkeypatch.setattr(
        "app.models.inventory.FurnitureType",
        {"dummy_item": type("Enum", (), {"value": 1})},
    )
    called = False

    def fake_update_furniture_amount_in_db(item, quantity, f_type_enum, sign):
        nonlocal called
        called = True
        assert item.__class__.__name__ == "DummyItem"
        assert quantity == 5
        assert f_type_enum == 1
        assert sign is True

    monkeypatch.setattr(
        inv, "update_furniture_amount_in_db", fake_update_furniture_amount_in_db
    )
    dummy = DummyItem()
    dummy.__class__.__name__ = "DummyItem"
    inv.update_amount_in_inventory(dummy, 5, True)
    assert called


def test_update_amount_in_inventory_invalid_item_none(inv):
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(None, 5, True)


def test_update_amount_in_inventory_invalid_quantity_type(inv):
    dummy = DummyItem()
    dummy.__class__.__name__ = "DummyItem"
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(dummy, "5", True)


def test_update_amount_in_inventory_invalid_sign_type(inv):
    dummy = DummyItem()
    dummy.__class__.__name__ = "DummyItem"
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(dummy, 5, "True")


def test_update_furniture_amount_in_db_increase(monkeypatch, inv):
    fake_session = MagicMock()
    fake_inventory_item = DummyInventoryDB(quantity=10)
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_inventory_item
    fake_session.query.return_value = fake_query
    monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        "app.models.inventory.get_index_furniture_by_values", lambda x: 42
    )
    inv.update_furniture_amount_in_db("dummy_item", 5, 1, True)
    assert fake_inventory_item.quantity == 15
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


def test_update_furniture_amount_in_db_decrease(monkeypatch, inv):
    fake_session = MagicMock()
    fake_inventory_item = DummyInventoryDB(quantity=20)
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_inventory_item
    fake_session.query.return_value = fake_query
    monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        "app.models.inventory.get_index_furniture_by_values", lambda x: 42
    )
    inv.update_furniture_amount_in_db("dummy_item", 5, 1, False)
    assert fake_inventory_item.quantity == 15
    fake_session.commit.assert_called_once()
    fake_session.close.assert_called_once()


def test_update_furniture_amount_in_db_item_not_found(monkeypatch, inv):
    fake_session = MagicMock()
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = None
    fake_session.query.return_value = fake_query
    monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        "app.models.inventory.get_index_furniture_by_values", lambda x: 42
    )
    inv.update_furniture_amount_in_db("dummy_item", 5, 1, True)
    fake_session.rollback.assert_called_once()
    fake_session.close.assert_called_once()


def test_get_information_by_query_invalid_types(inv):
    with pytest.raises(TypeError):
        inv.get_information_by_query(123, "value")
    with pytest.raises(TypeError):
        inv.get_information_by_query("column", 456)


def test_get_information_by_price_range_invalid_types(inv):
    with pytest.raises(TypeError):
        inv.get_information_by_price_range(min_price="0", max_price=100)
    with pytest.raises(TypeError):
        inv.get_information_by_price_range(min_price=0, max_price="100")


def test_get_information_by_price_range_found(monkeypatch, inv):
    flask_app = Flask(__name__)
    with flask_app.app_context():
        fake_session = MagicMock()
        fake_session.__enter__.return_value = fake_session
        fake_item1 = DummyInventoryDB(quantity=3, price=75)
        fake_item2 = DummyInventoryDB(quantity=8, price=85)
        fake_query = MagicMock()
        fake_query.filter.return_value.all.return_value = [fake_item1, fake_item2]
        fake_session.query.return_value = fake_query
        monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
        response = inv.get_information_by_price_range(50, 100)
        assert isinstance(response, Response)
        assert response.json == [
            {"quantity": 3, "price": 75},
            {"quantity": 8, "price": 85},
        ]
        fake_session.close.assert_called_once()


def test_get_information_by_price_range_no_results(monkeypatch, inv):
    flask_app = Flask(__name__)
    with flask_app.app_context():
        fake_session = MagicMock()
        fake_session.__enter__.return_value = fake_session
        fake_query = MagicMock()
        fake_query.filter.return_value.all.return_value = []
        fake_session.query.return_value = fake_query
        monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
        response = inv.get_information_by_price_range(50, 100)
        assert response is None
        fake_session.close.assert_called_once()
