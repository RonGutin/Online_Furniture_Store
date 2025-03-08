import pytest
from flask import Flask
from unittest.mock import MagicMock
from app.models.inventory import Inventory


class DummyItem:
    """
    A simple dummy class used as a placeholder for furniture items in tests.
    """

    pass


class DummyInventoryDB:
    """
    A test double for the InventoryDB database model.

    Simulates the structure and behavior of the InventoryDB model
    without requiring the actual database connection.

    Attributes:
        quantity (int): The inventory quantity
        price (int): The item price
    """

    def __init__(self, quantity, price=100):
        self.quantity = quantity
        self.price = price

    def to_dict(self):
        """
        Convert the instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the quantity and price
        """
        return {"quantity": self.quantity, "price": self.price}


@pytest.fixture(autouse=True)
def reset_inventory_singleton():
    """
    Reset the Inventory singleton instance before each test.

    This ensures that each test works with a fresh Inventory instance.
    """
    Inventory._instance = None


@pytest.fixture
def inv():
    """
    Fixture that provides an Inventory instance for testing.

    Returns:
        Inventory: A fresh instance of the Inventory class
    """
    return Inventory()


def test_update_amount_in_inventory_valid(monkeypatch, inv):
    """
    Test update_amount_in_inventory with valid parameters.

    Verifies that the method calls update_furniture_amount_in_db with correct parameters.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
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
    """
    Test update_amount_in_inventory with None as the item parameter.

    Verifies that the method raises TypeError when item is None.

    Args:
        inv: The Inventory fixture
    """
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(None, 5, True)


def test_update_amount_in_inventory_invalid_quantity_type(inv):
    """
    Test update_amount_in_inventory with a non-integer quantity.

    Verifies that the method raises TypeError when quantity is not an integer.

    Args:
        inv: The Inventory fixture
    """
    dummy = DummyItem()
    dummy.__class__.__name__ = "DummyItem"
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(dummy, "5", True)


def test_update_amount_in_inventory_invalid_sign_type(inv):
    """
    Test update_amount_in_inventory with a non-boolean sign.

    Verifies that the method raises TypeError when sign is not a boolean.

    Args:
        inv: The Inventory fixture
    """
    dummy = DummyItem()
    dummy.__class__.__name__ = "DummyItem"
    with pytest.raises(TypeError):
        inv.update_amount_in_inventory(dummy, 5, "True")


def test_update_furniture_amount_in_db_increase(monkeypatch, inv):
    """
    Test update_furniture_amount_in_db when increasing inventory quantity.

    Verifies that the method correctly increases the quantity and commits the change.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
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
    """
    Test update_furniture_amount_in_db when decreasing inventory quantity.

    Verifies that the method correctly decreases the quantity and commits the change.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
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
    """
    Test update_furniture_amount_in_db when the item is not found in the database.

    Verifies that the method rolls back the transaction when the item isn't found.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
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
    """
    Test get_information_by_query with invalid parameter types.

    Verifies that the method raises TypeError when parameters are of incorrect types.

    Args:
        inv: The Inventory fixture
    """
    with pytest.raises(TypeError):
        inv.get_information_by_query(123, "value")
    with pytest.raises(TypeError):
        inv.get_information_by_query("column", 456)


def test_get_information_by_price_range_invalid_types(inv):
    """
    Test get_information_by_price_range with invalid parameter types.

    Verifies that the method raises TypeError when min_price or max_price are not numbers.

    Args:
        inv: The Inventory fixture
    """
    with pytest.raises(TypeError):
        inv.get_information_by_price_range(min_price="0", max_price=100)
    with pytest.raises(TypeError):
        inv.get_information_by_price_range(min_price=0, max_price="100")


def test_get_information_by_price_range_found(monkeypatch, inv):
    """
    Test get_information_by_price_range when items are found.

    Verifies that the method returns the expected list of items when items are found.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
    flask_app = Flask(__name__)
    with flask_app.app_context():
        fake_session = MagicMock()
        fake_session.__enter__.return_value = fake_session
        # Create fake InventoryDB objects that will be converted to dicts
        fake_item1 = MagicMock()
        fake_item1.__dict__ = {
            "quantity": 3,
            "price": 75,
            "_sa_instance_state": object(),
        }
        fake_item2 = MagicMock()
        fake_item2.__dict__ = {
            "quantity": 8,
            "price": 85,
            "_sa_instance_state": object(),
        }

        fake_query = MagicMock()
        fake_query.filter.return_value.all.return_value = [fake_item1, fake_item2]
        fake_session.query.return_value = fake_query
        monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)

        response = inv.get_information_by_price_range(50, 100)
        # Test now expects a list directly, not a Response object
        assert isinstance(response, list)
        assert response == [
            {"quantity": 3, "price": 75},
            {"quantity": 8, "price": 85},
        ]
        fake_session.close.assert_called_once()


def test_get_information_by_price_range_no_results(monkeypatch, inv):
    """
    Test get_information_by_price_range when no items are found.

    Verifies that the method returns an empty list when no items match the criteria.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
    flask_app = Flask(__name__)
    with flask_app.app_context():
        fake_session = MagicMock()
        fake_session.__enter__.return_value = fake_session
        fake_query = MagicMock()
        fake_query.filter.return_value.all.return_value = []
        fake_session.query.return_value = fake_query
        monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)

        response = inv.get_information_by_price_range(50, 100)
        # The function now returns an empty list instead of None when no results are found
        assert response == []
        fake_session.close.assert_called_once()


def test_update_furniture_amount_in_db_empty_quantity(monkeypatch, inv):
    """
    Test updating inventory with zero quantity.

    Verifies that updating with quantity=0 makes no changes to the inventory quantity.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
    fake_session = MagicMock()
    fake_inventory_item = MagicMock()
    fake_inventory_item.quantity = 10
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_inventory_item
    fake_session.query.return_value = fake_query

    monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        "app.models.inventory.get_index_furniture_by_values", lambda x: 42
    )

    # Update with quantity=0
    inv.update_furniture_amount_in_db("dummy_item", 0, 1, True)

    # Verify quantity remains unchanged
    assert fake_inventory_item.quantity == 10
    # Verify commit was still called
    fake_session.commit.assert_called_once()


def test_inventory_singleton_pattern():
    """
    Test that the Inventory class follows the singleton pattern.

    Verifies that multiple instantiations of Inventory return the same instance.
    """
    inv1 = Inventory()
    inv2 = Inventory()
    assert inv1 is inv2, "Inventory should be a singleton"


def test_update_furniture_amount_in_db_sign_false(monkeypatch, inv):
    """
    Test updating inventory with sign=False (decrease quantity).

    Verifies that the method correctly decreases the quantity when sign is False.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
        inv: The Inventory fixture
    """
    fake_session = MagicMock()
    fake_inventory_item = MagicMock()
    fake_inventory_item.quantity = 10
    fake_query = MagicMock()
    fake_query.filter.return_value.first.return_value = fake_inventory_item
    fake_session.query.return_value = fake_query

    monkeypatch.setattr("app.models.inventory.SessionLocal", lambda: fake_session)
    monkeypatch.setattr(
        "app.models.inventory.get_index_furniture_by_values", lambda x: 42
    )

    # Update with sign=False to decrease
    inv.update_furniture_amount_in_db("dummy_item", 3, 1, False)

    # Verify quantity was decreased
    assert fake_inventory_item.quantity == 7
    fake_session.commit.assert_called_once()
