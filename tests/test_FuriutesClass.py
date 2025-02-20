import pytest
from unittest.mock import patch
from app.models.FurnituresClass import (
    DiningTable,
    WorkDesk,
    CoffeeTable,
    GamingChair,
    WorkChair,
)


@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch("app.data.DbConnection.SessionLocal"):
        yield


@pytest.fixture
def furniture_objects():
    with patch.object(
        DiningTable, "check_availability", return_value=True
    ), patch.object(WorkDesk, "check_availability", return_value=True), patch.object(
        CoffeeTable, "check_availability", return_value=True
    ), patch.object(
        GamingChair, "check_availability", return_value=True
    ), patch.object(
        WorkChair, "check_availability", return_value=True
    ):
        return {
            "dining_table": DiningTable(color="brown", material="wood"),
            "work_desk": WorkDesk(color="black", material="wood"),
            "coffee_table": CoffeeTable(color="gray", material="glass"),
            "gaming_chair": GamingChair(
                color="black", is_adjustable=True, has_armrest=True
            ),
            "work_chair": WorkChair(color="red", is_adjustable=True, has_armrest=False),
        }


def test_valid_furniture_creation(furniture_objects):
    assert isinstance(furniture_objects["dining_table"], DiningTable)
    assert isinstance(furniture_objects["work_desk"], WorkDesk)
    assert isinstance(furniture_objects["coffee_table"], CoffeeTable)
    assert isinstance(furniture_objects["gaming_chair"], GamingChair)
    assert isinstance(furniture_objects["work_chair"], WorkChair)


@pytest.mark.parametrize("color, material", [("Purple", "wood"), ("Green", "wood")])
def test_invalid_color(color, material):
    with pytest.raises(ValueError):
        DiningTable(color=color, material=material)


@pytest.mark.parametrize(
    "color, material",
    [
        ("brown", "Plastic"),
        ("gray", "Wood"),
    ],
)
def test_invalid_material(color, material):
    with pytest.raises(ValueError):
        CoffeeTable(color=color, material=material)


def test_calculate_discount(furniture_objects):
    dining_table = furniture_objects["dining_table"]
    dining_table.price = 1000.0
    assert dining_table.calculate_discount(10) == 900.0
    assert dining_table.calculate_discount(100) == 0.0
    with pytest.raises(ValueError):
        dining_table.calculate_discount(-5)


def test_apply_tax(furniture_objects):
    dining_table = furniture_objects["dining_table"]
    dining_table.price = 1000.0
    assert dining_table.apply_tax(10) == 1100.0
    with pytest.raises(ValueError):
        dining_table.apply_tax(-8)


def test_check_availability(furniture_objects):
    assert furniture_objects["dining_table"].check_availability(amount=1) is True
    assert furniture_objects["gaming_chair"].check_availability(amount=2) is True


def test_get_color(furniture_objects):
    assert furniture_objects["dining_table"].get_color() == "brown"
    assert furniture_objects["work_desk"].get_color() == "black"
    assert furniture_objects["gaming_chair"].get_color() == "black"


@pytest.mark.parametrize("price, expected", [(1500.0, 1500.0), (2000.0, 2000.0)])
def test_get_price(price, expected, furniture_objects):
    dining_table = furniture_objects["dining_table"]
    dining_table.price = price
    assert dining_table.get_price() == expected

    dining_table.price = None
    with pytest.raises(ValueError):
        dining_table.get_price()
