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


@pytest.mark.parametrize("price, expected", [(1500.0, 1500.0), (2000.0, 2000.0)])
def test_get_price(price, expected, furniture_objects):
    dining_table = furniture_objects["dining_table"]
    dining_table.price = price
    assert dining_table.get_price() == expected

    dining_table.price = None
    with pytest.raises(ValueError):
        dining_table.get_price()


@patch("app.models.FurnituresClass.Inventory")
def test_check_availability(mock_inventory, furniture_objects):
    mock_inventory_instance = MagicMock()
    mock_inventory.return_value = mock_inventory_instance
    mock_inventory_instance.get_index_furniture_by_values.return_value = 1

    with patch("app.models.FurnituresClass.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = (10,)

        assert furniture_objects["dining_table"].check_availability(amount=1) is True
        assert furniture_objects["dining_table"].check_availability(amount=11) is False


@patch("app.models.FurnituresClass.SessionLocal")
def test_get_match_furniture(mock_session, furniture_objects):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_session.return_value.__enter__.return_value = mock_db
    mock_query = MagicMock()
    mock_db.query.return_value.filter.return_value = mock_query

    mock_query.first.return_value = (10, "Great Chair", True, True)

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

    furniture_objects["dining_table"].Print_matching_product_advertisement()

    printed_texts = [call_arg[0][0] for call_arg in mock_print.call_args_list]

    expected_text = (
        "*** SPECIAL OFFER !!! ***\n"
        "We found a matching chair for your table!\n"
        "Description: Amazing Chair\n"
        "Adjustable: Yes\n"
        "Has Armrest: Yes\n"
        "It's the perfect chair for you, and it's in stock!"
    )

    assert any(expected_text in text for text in printed_texts)
