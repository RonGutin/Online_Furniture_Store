import pytest
from unittest.mock import patch
from app.utils import get_index_furniture_by_values


class FakeDiningTable:
    def __init__(self, color, dimensions, material=None):
        self.color = color
        self.dimensions = dimensions
        self.material = material

    @property
    def __class__(self):
        class Fake:
            __name__ = "DiningTable"

        return Fake


@pytest.mark.integration
@patch("app.utils.transform_pascal_to_snake", return_value="DINING_TABLE")
def test_get_index_furniture_by_values_existing_table(mocked_transform):
    table = FakeDiningTable(color="brown", dimensions=(100, 50, 60), material="wood")
    returned_id = get_index_furniture_by_values(table)
    assert returned_id == 1, f"Expected ID=1, got {returned_id}"


@pytest.mark.integration
def test_get_index_furniture_by_values_not_found():
    table = FakeDiningTable(color="brown", dimensions=(999, 999, 999), material="wood")
    returned_id = get_index_furniture_by_values(table)
    assert returned_id is None, f"Expected None, got {returned_id}"


class FakeGamingChair:
    def __init__(self, color, dimensions, is_adjustable, has_armrest):
        self.color = color
        self.dimensions = dimensions
        self.is_adjustable = is_adjustable
        self.has_armrest = has_armrest

    @property
    def __class__(self):
        class Fake:
            __name__ = "GamingChair"

        return Fake


@pytest.mark.integration
@patch("app.utils.transform_pascal_to_snake", return_value="GAMING_CHAIR")
def test_get_index_furniture_by_values_existing_chair(mocked_transform):

    chair = FakeGamingChair(
        color="blue", dimensions=(150, 70, 80), is_adjustable=True, has_armrest=True
    )
    returned_id = get_index_furniture_by_values(chair)
    assert returned_id == 25, f"Expected ID=25, got {returned_id}"
