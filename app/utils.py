import re
from typing import Optional
from sqlalchemy import and_

from app.data.DbConnection import SessionLocal, InventoryDB


def transform_pascal_to_snake(text: str) -> str:
    """
    Converts a PascalCase string to SNAKE_CASE.

    Args:
        text (str): The PascalCase string.

    Returns:
        str: The converted SNAKE_CASE string.
    """
    text = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
    return text.upper()


def get_index_furniture_by_values(item) -> Optional[int]:
    """
    Retrieves the index (ID) of a furniture item in InventoryDB based on its attributes.

    Args:
        item: An instance of a furniture class.

    Returns:
        Optional[int]: The ID if found, otherwise None.
    """
    if item is None:
        print("Error: item is None")
        return None

    ans: Optional[int] = None

    try:
        furniture_type = transform_pascal_to_snake(item.__class__.__name__)

        with SessionLocal() as session:
            filters = [
                InventoryDB.furniture_type == furniture_type,
                InventoryDB.color == item.color,
                InventoryDB.high == item.dimensions[0],
                InventoryDB.depth == item.dimensions[1],
                InventoryDB.width == item.dimensions[2],
            ]

            # Add optional attributes only if they exist
            if hasattr(item, "is_adjustable"):
                filters.append(InventoryDB.is_adjustable == item.is_adjustable)
            if hasattr(item, "has_armrest"):
                filters.append(InventoryDB.has_armrest == item.has_armrest)
            if hasattr(item, "material"):
                filters.append(InventoryDB.material == item.material)

            result = session.query(InventoryDB.id).filter(and_(*filters)).first()
            if result:
                ans = result[0]

    except Exception as e:
        print(f"Error fetching data: {e}")

    finally:
        return ans
