import pytest
from unittest.mock import patch
from app.utils import transform_pascal_to_snake
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
    """
    Fixture to mock the database connection for all tests.

    Automatically applied to all tests to avoid actual database connections.

    Yields:
        None
    """
    with patch("app.data.DbConnection.SessionLocal"):
        yield


@pytest.fixture
def furniture_factory():
    """
    Fixture that provides a FurnitureFactory instance for testing.

    Returns:
        FurnitureFactory: An instance of the FurnitureFactory class.
    """
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
    """
    Test creating different types of furniture using the factory.

    Verifies that the factory creates the correct furniture class instance
    and that the instance has the expected properties.

    Args:
        furniture_factory: The FurnitureFactory fixture.
        furniture_type (str): The type of furniture to create.
        expected_class: The expected class of the created furniture.
        kwargs (dict): The parameters to pass to the factory.
    """
    furniture = furniture_factory.create_furniture(furniture_type, **kwargs)
    assert isinstance(furniture, expected_class)
    for key, value in kwargs.items():
        assert getattr(furniture, key) == value


def test_invalid_furniture_type(furniture_factory):
    """
    Test creating furniture with an invalid type.

    Verifies that the factory raises a ValueError when an invalid
    furniture type is provided.

    Args:
        furniture_factory: The FurnitureFactory fixture.
    """
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
    """
    Test creating furniture with missing required parameters.

    Verifies that the factory raises a TypeError when required parameters
    are missing (material for DINING_TABLE or has_armrest for WORK_CHAIR).

    Args:
        furniture_factory: The FurnitureFactory fixture.
        furniture_type (str): The type of furniture to create.
        kwargs (dict): The incomplete parameters to pass to the factory.
    """
    with pytest.raises(TypeError):
        furniture_factory.create_furniture(furniture_type, **kwargs)


@pytest.mark.parametrize(
    "furniture_type, color, material",
    [
        ("COFFEE_TABLE", 123, "glass"),
        ("WORK_DESK", "black", None),
    ],
)
def test_invalid_parameter_type(furniture_factory, furniture_type, color, material):
    """
    Test creating furniture with invalid parameter types.

    Verifies that the factory raises a TypeError when parameters
    have invalid types (non-string color or None material).

    Args:
        furniture_factory: The FurnitureFactory fixture.
        furniture_type (str): The type of furniture to create.
        color: The color parameter with an invalid type.
        material: The material parameter with an invalid type.
    """
    with pytest.raises(TypeError):
        furniture_factory.create_furniture(
            furniture_type, color=color, material=material
        )


# Testing a function from the utils file
def test_basic_transformation():
    """
    Test basic PascalCase to SNAKE_CASE transformation.

    Verifies that the transform_pascal_to_snake function correctly
    transforms 'PascalCase' to 'PASCAL_CASE'.
    """
    assert transform_pascal_to_snake("PascalCase") == "PASCAL_CASE"


def test_single_word():
    """
    Test transformation of a single word.

    Verifies that the transform_pascal_to_snake function correctly
    transforms a single word 'Hello' to uppercase 'HELLO'.
    """
    assert transform_pascal_to_snake("Hello") == "HELLO"


def test_all_lowercase():
    """
    Test transformation of an all lowercase word.

    Verifies that the transform_pascal_to_snake function correctly
    transforms an all lowercase word 'lowercase' to uppercase 'LOWERCASE'.
    """
    assert transform_pascal_to_snake("lowercase") == "LOWERCASE"
