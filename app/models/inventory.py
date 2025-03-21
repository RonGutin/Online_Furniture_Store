from typing import Optional
from flask import jsonify, Response
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.data.DbConnection import SessionLocal, InventoryDB
from app.models.EnumsClass import FurnitureType
from app.utils import transform_pascal_to_snake, get_index_furniture_by_values


class Inventory:
    """Singleton class for managing inventory."""

    _instance: Optional["Inventory"] = None

    def __new__(cls) -> "Inventory":
        """Ensures only one instance of Inventory exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def update_amount_in_inventory(
        self, item: object, quantity: int, sign: int
    ) -> None:
        """
        Updates the quantity of a furniture item in inventory.

        Args:
            item (object): The furniture item whose quantity needs to be updated.
            quantity (int): The amount to add or subtract from the inventory.
            sign (bool): If True, increases quantity; if False, decreases it.

        """
        if item is not None and not hasattr(item, "__class__"):
            raise TypeError("Invalid item: Expected an object with a class type.")
        if item is None:
            raise TypeError("Error: No item provided.")
        if not isinstance(quantity, int):
            raise TypeError("quantity must be a number.")
        if not isinstance(sign, int):
            raise TypeError("sign must be a True/False.")

        furniture_type: str = transform_pascal_to_snake(item.__class__.__name__)
        f_type_enum: int = FurnitureType[furniture_type].value

        self.update_furniture_amount_in_db(item, quantity, f_type_enum, sign)

    def update_furniture_amount_in_db(
        self, item: str, quantity: int, f_type_enum: int, sign: bool
    ) -> None:  # calls from "update_amount_in_inventory" - validation before calling
        """
        Updates the quantity field for a specific furniture item (Chair/Table) in the InventoryDB.

        Args:
            item (str): The name or identifier of the furniture item.
            quantity (int): The amount to be added or subtracted from the inventory.
            f_type_enum (int): An integer representing the furniture type.
            sign (bool): A boolean indicating the action:
                        - True (1) if a manager is updating inventory,
                        - False (0) if a user is making a checkout.

        Raises:
            ValueError: If the furniture item is not found in the inventory.
        """
        session: Session = SessionLocal()
        try:
            item_id = get_index_furniture_by_values(item)
            inventory_item = (
                session.query(InventoryDB).filter(InventoryDB.id == item_id).first()
            )

            if inventory_item:
                if sign:
                    inventory_item.quantity += quantity
                else:
                    inventory_item.quantity -= quantity

                session.commit()
            else:
                raise ValueError(f"Item: {item} not found in inventory.")

        except Exception as e:
            session.rollback()
            print(f"Error in updating furniture quantity in DB: {e}")

        finally:
            session.close()

    def get_information_by_query(
        self, column: str, column_value: str
    ) -> Optional[list]:
        """
        Fetches information from the InventoryDB based on a dynamic column and its value.

        Args:
            column (str): The column name to filter by (e.g., 'f_type').
            column_value (str): The value to search for in the specified column (e.g., 'Chair').

        Returns:
            list | None: A list of results in JSON format, or None if no matching data is found.

        Raises:
            ValueError: If the column does not exist in the table.
        """
        if not isinstance(column, str):
            raise TypeError("Expected column to be a string.")
        if not isinstance(column_value, str):
            raise TypeError("Expected column_value to be a string.")

        ans: Response | None = None
        try:
            with SessionLocal() as session:
                col = getattr(InventoryDB, column, None)
                if col is None:
                    raise ValueError(f"Column '{column}' does not exist in the table.")

                result = session.query(InventoryDB).filter(col == column_value).all()

                if result:
                    json_data = []
                    for row in result:
                        json_data.append(row.to_dict())
                    ans = jsonify(json_data)

        except Exception as e:
            print(f"Error fetching data: {e}")

        return ans

    def get_information_by_price_range(
        self, min_price: float = 0, max_price: float = float("inf")
    ) -> Optional[Response]:
        """
        Fetches furniture items from the InventoryDB within a specific price range.

        Args:
            min_price (float): The minimum price for the furniture item. Defaults to 0.
            max_price (float): The maximum price for the furniture item. Defaults to infinity.

        Returns:
            Response | None: A Flask Response object in JSON format,
            or None if no matching data is found.
        """

        if not isinstance(min_price, (int, float)):
            raise TypeError("Expected min_price to be a number.")
        if not isinstance(max_price, (int, float)):
            raise TypeError("Expected max_price to be a number.")

        ans: Response | None = None  # Declaring ans with the correct type hint

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
                json_data = []
                if result:

                    for row in result:
                        # Assuming here you want to format the row to JSON
                        row_dict = row.__dict__
                        row_dict.pop("_sa_instance_state", None)
                        json_data.append(
                            row_dict
                        )  # Example conversion, adjust according to actual logic
                ans = json_data

        except Exception as e:
            print(f"Error fetching data: {e}")

        finally:
            session.close()
            return ans
