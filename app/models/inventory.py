from cmath import inf
from typing import Optional

from flask import jsonify
from sqlalchemy import and_

from app.utils import transform_pascal_to_snake
from app.models.EnumsClass import FurnitureType
from app.data.DbConnection import SessionLocal, InventoryDB


class Inventory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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

                return result[0] if result else None

        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def update_amount_in_inventory(self, item, quantity: int, sign: bool) -> None:
        """
        Determines the furniture type and updates its quantity in inventory.
        """
        if item is None:
            print("Error: No item provided.")
            return
        furniture_type = transform_pascal_to_snake(item.__class__.__name__)
        f_type_enum = FurnitureType[furniture_type].value
        self.update_furniture_amount_in_DB(item, quantity, f_type_enum, sign)

    def update_furniture_amount_in_DB(
        self, item, quantity: int, f_type_enum: int, sign: bool
    ) -> None:
        """
        Updates quantity field for a specific furniture item (Chair/Table) in the InventoryDB.
        sign - boolean that points if it is a user making a checkout (sign = 0)
        or a manager updating inventory (sign = 1)
        """
        session = SessionLocal()
        try:
            item_id = self.get_index_furniture_by_values(item)
            invetory_item = (
                session.query(InventoryDB).filter(InventoryDB.id == item_id).first()
            )

            if invetory_item:
                if sign:
                    invetory_item.quantity += quantity
                else:
                    invetory_item.quantity -= quantity

                session.commit()
            else:
                raise ValueError(f"Item: {item} not found in inventory.")

        except Exception as e:
            session.rollback()
            print(f"Error in updating furniture quantity in DB: {e}")
        finally:
            session.close()

    def get_information_by_query(
        self, column, column_value
    ):  # coulmn = f_type, coulmn_value= Chair
        ans = None
        try:
            with SessionLocal() as session:
                col = getattr(InventoryDB, column, None)
                if col is None:
                    raise ValueError(f"Column '{column}' does not exist in the table.")
                else:
                    result = (
                        session.query(InventoryDB).filter(col == column_value).all()
                    )
                    if result:
                        json_data = []
                        for row in result:
                            pass  # !
                        ans = jsonify(json_data)
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            session.close()
            return ans

    def get_information_by_price_range(self, min_price=0, max_price=inf):
        ans = None
        try:
            with SessionLocal() as session:
                result = (
                    session.query(InventoryDB)
                    .filter(
                        and_(
                            InventoryDB.price >= min_price,
                            InventoryDB.price <= max_price,
                        )
                    )
                    .all()
                )
                if result:
                    json_data = []
                    for row in result:
                        pass  # !
                    ans = jsonify(json_data)
                else:
                    pass
        # !
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            session.close()
            return ans
