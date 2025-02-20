import pytest
from unittest.mock import patch
from app.models.FurnitureFactory import FurnitureFactory
from app.models.FurnituresClass import (
    DiningTable,
    WorkDesk,
    CoffeeTable,
    WorkChair,
    GamingChair,
)


@pytest.fixture(autouse=True)
def mock_db_connection():
    """מונע גישה אמיתית ל-DB"""
    with patch("app.data.DbConnection.SessionLocal"):
        yield


@pytest.fixture
def furniture_factory():
    """יוצר מופע של המפעל"""
    return FurnitureFactory()


@pytest.mark.parametrize(
    "furniture_type, expected_class, kwargs",
    [
        ("DINING_TABLE", DiningTable, {"color": "brown", "material": "wood"}),
        ("WORK_DESK", WorkDesk, {"color": "white", "material": "glass"}),
        ("COFFEE_TABLE", CoffeeTable, {"color": "gray", "material": "plastic"}),
        (
            "WORK_CHAIR",
            WorkChair,
            {"color": "red", "is_adjustable": True, "has_armrest": False},
        ),
        (
            "GAMING_CHAIR",
            GamingChair,
            {"color": "black", "is_adjustable": True, "has_armrest": True},
        ),
    ],
)
def test_create_furniture(furniture_factory, furniture_type, expected_class, kwargs):
    """בדיקת יצירת רהיטים מסוגים שונים"""
    furniture = furniture_factory.create_furniture(furniture_type, **kwargs)
    assert isinstance(furniture, expected_class)
    for key, value in kwargs.items():
        assert getattr(furniture, key) == value


def test_invalid_furniture_type(furniture_factory):
    """בדיקה שניסיון ליצור רהיט לא תקין זורק ValueError"""
    with pytest.raises(ValueError):
        furniture_factory.create_furniture("SOFA", color="brown", material="wood")


@pytest.mark.parametrize(
    "furniture_type, kwargs",
    [
        ("DINING_TABLE", {"color": "brown"}),  # חסר חומר
        ("WORK_CHAIR", {"color": "black", "is_adjustable": True}),  # חסר ידיות
    ],
)
def test_missing_parameter(furniture_factory, furniture_type, kwargs):
    """בדיקה שניסיון ליצור רהיט עם פרמטרים חסרים זורק TypeError"""
    with pytest.raises(TypeError):
        furniture_factory.create_furniture(furniture_type, **kwargs)


@pytest.mark.parametrize(
    "furniture_type, color, material",
    [
        ("COFFEE_TABLE", 123, "glass"),  # צבע צריך להיות מחרוזת
        ("WORK_DESK", "black", None),  # חומר לא יכול להיות None
    ],
)
def test_invalid_parameter_type(furniture_factory, furniture_type, color, material):
    """בדיקה שסוגי קלט לא חוקיים זורקים TypeError"""
    with pytest.raises(TypeError):
        furniture_factory.create_furniture(
            furniture_type, color=color, material=material
        )
