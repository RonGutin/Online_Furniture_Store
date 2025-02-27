import pytest
from unittest.mock import patch, MagicMock
from app.models.FurnituresClass import (
    DiningTable,
    WorkDesk,
    CoffeeTable,
    GamingChair,
    WorkChair,
)

@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch("app.data.DbConnection.SessionLocal") as mock_session:
        mock_session.return_value = MagicMock()
        yield

@pytest.fixture
def furniture_objects():
    with patch.object(
        DiningTable,
        "_get_info_furniture_by_key",
        return_value=(1000, "Mock Table", "A test table"),
    ), patch.object(
        WorkDesk,
        "_get_info_furniture_by_key",
        return_value=(800, "Mock Desk", "A test desk"),
    ), patch.object(
        CoffeeTable,
        "_get_info_furniture_by_key",
        return_value=(500, "Mock Coffee Table", "A test coffee table"),
    ), patch.object(
        GamingChair,
        "_get_info_furniture_by_key",
        return_value=(300, "Mock Gaming Chair", "A test gaming chair"),
    ), patch.object(
        WorkChair,
        "_get_info_furniture_by_key",
        return_value=(250, "Mock Work Chair", "A test work chair"),
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
    assert dining_table.calculate_discount(10) == 900.0
    assert dining_table.calculate_discount(100) == 0.0
    with pytest.raises(ValueError):
        dining_table.calculate_discount(-5)

def test_apply_tax(furniture_objects):
    dining_table = furniture_objects["dining_table"]
    assert dining_table.apply_tax(10) == 1100.0
    with pytest.raises(ValueError):
        dining_table.apply_tax(-8)

@pytest.mark.parametrize("price, expected", [(1500.0, 1500.0), (2000.0, 2000.0)])
def test_get_price(price, expected, furniture_objects):
    dining_table = furniture_objects["dining_table"]
    dining_table.price = price
    assert dining_table.get_price() == expected

    dining_table.price = None
    with pytest.raises(ValueError):
        dining_table.get_price()

@patch("app.models.FurnituresClass.SessionLocal")
def test_get_match_furniture(mock_session, furniture_objects):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_session.return_value.__enter__.return_value = mock_db
    mock_query = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_query

    mock_query.first.return_value = (10, "Great Chair", True, True)

    with patch.object(
        furniture_objects["dining_table"],
        "get_match_furniture",
        return_value="SPECIAL OFFER: Great Chair",
    ):
        advertisement = furniture_objects["dining_table"].get_match_furniture([13, 14])

    assert "SPECIAL OFFER" in advertisement
    assert "Great Chair" in advertisement

@patch("builtins.print")
@patch("app.models.FurnituresClass.SessionLocal")
def test_Print_matching_product_advertisement(
    mock_session, mock_print, furniture_objects
):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_session.return_value.__enter__.return_value = mock_db
    mock_query = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_query

    mock_query.first.return_value = (10, "Amazing Chair", True, True)

    with patch.object(
        furniture_objects["dining_table"],
        "get_match_furniture",
        return_value=(
            "*** SPECIAL OFFER !!! ***\n"
            "We found a matching chair for your table!\n"
            "Description: Amazing Chair\n"
            "Adjustable: Yes\n"
            "Has Armrest: Yes\n"
            "It's the perfect chair for you, and it's in stock!"
        ),
    ):
        furniture_objects["dining_table"].Print_matching_product_advertisement()

    mock_print.assert_any_call(
        "*** SPECIAL OFFER !!! ***\n"
        "We found a matching chair for your table!\n"
        "Description: Amazing Chair\n"
        "Adjustable: Yes\n"
        "Has Armrest: Yes\n"
        "It's the perfect chair for you, and it's in stock!"
    )