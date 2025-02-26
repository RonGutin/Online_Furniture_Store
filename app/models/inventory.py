from cmath import inf
from typing import Optional

from flask import jsonify
from sqlalchemy import and_

from app.utils import transform_pascal_to_snake
from app.models.EnumsClass import FurnitureType
from app.data.DbConnection import SessionLocal, InventoryDB
from app.utils import get_index_furniture_by_values


class Inventory:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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
            item_id = get_index_furniture_by_values(item)
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
