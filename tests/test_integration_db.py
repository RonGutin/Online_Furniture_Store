import pytest
from unittest.mock import patch
from app.utils import get_index_furniture_by_values


class FakeDiningTable:
    """
    A test double class representing a DiningTable for testing purposes.

    This class mimics the essential properties of a DiningTable from the
    FurnituresClass module without requiring the actual implementation.

    Attributes:
        color (str): The color of the dining table
        dimensions (tuple): The dimensions of the table (width, height, depth)
        material (str): The material of the table (wood, glass, etc.)
    """

    def __init__(self, color, dimensions, material=None):
        self.color = color
        self.dimensions = dimensions
        self.material = material

    @property
    def __class__(self):
        """
        Overrides the __class__ property to make the object appear as a DiningTable.

        Returns:
            A fake class object with __name__ set to "DiningTable"
        """

        class Fake:
            __name__ = "DiningTable"

        return Fake


@pytest.mark.integration
@patch("app.utils.transform_pascal_to_snake", return_value="DINING_TABLE")
def test_get_index_furniture_by_values_existing_table(mocked_transform):
    """
    Integration test for get_index_furniture_by_values with an existing DiningTable.

    Tests that the function correctly identifies a table with known properties
    and returns the expected database ID.

    Args:
        mocked_transform: Mocked transform_pascal_to_snake function that returns "DINING_TABLE"
    """
    table = FakeDiningTable(color="brown", dimensions=(100, 50, 60), material="wood")
    returned_id = get_index_furniture_by_values(table)
    assert returned_id == 1, f"Expected ID=1, got {returned_id}"


@pytest.mark.integration
def test_get_index_furniture_by_values_not_found():
    """
    Integration test for get_index_furniture_by_values with a non-existent furniture item.

    Tests that the function returns None when the furniture item doesn't exist in the database.
    """
    table = FakeDiningTable(color="brown", dimensions=(999, 999, 999), material="wood")
    returned_id = get_index_furniture_by_values(table)
    assert returned_id is None, f"Expected None, got {returned_id}"


class FakeGamingChair:
    """
    A test double class representing a GamingChair for testing purposes.

    This class mimics the essential properties of a GamingChair from the
    FurnituresClass module without requiring the actual implementation.

    Attributes:
        color (str): The color of the gaming chair
        dimensions (tuple): The dimensions of the chair (width, height, depth)
        is_adjustable (bool): Whether the chair is height adjustable
        has_armrest (bool): Whether the chair has armrests
    """

    def __init__(self, color, dimensions, is_adjustable, has_armrest):
        self.color = color
        self.dimensions = dimensions
        self.is_adjustable = is_adjustable
        self.has_armrest = has_armrest

    @property
    def __class__(self):
        """
        Overrides the __class__ property to make the object appear as a GamingChair.

        Returns:
            A fake class object with __name__ set to "GamingChair"
        """

        class Fake:
            __name__ = "GamingChair"

        return Fake


@pytest.mark.integration
@patch("app.utils.transform_pascal_to_snake", return_value="GAMING_CHAIR")
def test_get_index_furniture_by_values_existing_chair(mocked_transform):
    """
    Integration test for get_index_furniture_by_values with an existing GamingChair.

    Tests that the function correctly identifies a chair with known properties
    and returns the expected database ID.

    Args:
        mocked_transform: Mocked transform_pascal_to_snake function that returns "GAMING_CHAIR"
    """
    chair = FakeGamingChair(
        color="blue", dimensions=(150, 70, 80), is_adjustable=True, has_armrest=True
    )
    returned_id = get_index_furniture_by_values(chair)
    assert returned_id == 25, f"Expected ID=25, got {returned_id}"
