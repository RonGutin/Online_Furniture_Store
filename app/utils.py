import re
from typing import Optional
from app.data.DbConnection import SessionLocal, InventoryDB
from sqlalchemy import and_


def transform_pascal_to_snake(text):
    """_summary_

    Args:
        text (_type_): _description_

    Returns:
        _type_: _description_
    """
    text = re.sub(r"([a-z])([A-Z])", r"\1_\2", text)
    return text.upper()


def get_index_furniture_by_values(self, item) -> Optional[int]:
    """
    Retrieves the index (ID) of a furniture item in
    InventoryDB based on its attributes.
    Returns:
        - The ID if found.
        - None if no match exists.
    """
    if item is None:
        print("Error: item is None")
        return None
    ans = None
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
        session.close()
        return ans
