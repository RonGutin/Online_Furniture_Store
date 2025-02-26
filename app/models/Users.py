from abc import ABC, abstractmethod
from sqlalchemy import Column, Integer, String, Float, ForeignKey, and_
from sqlalchemy.orm import relationship
import re
from typing import Optional, List, Union
from datetime import datetime
from app.models.ShoppingCart import ShoppingCart
from app.data.DbConnection import (
    SessionLocal,
    UserDB,
    BasicUserDB,
    ManagerDB,
    OrdersDB,
    InventoryDB,
)
from app.models.Authentication import Authentication
from app.models.EnumsClass import OrderStatus, FurnitureType
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.FurnituresClass import Chair, Table


class BasicUser(ABC):

    def __init__(self, name: str, email: str, password: str):
        """
        Initialize a new User instance.
        Note: This should only be called by the Authentication class.
        """
        self.name = name
        self.email = self._validate_email(email)
        self.password = password  # Already hashed by Authentication

    def _validate_email(self, email: str) -> str:
        """
        Validate email format using regex.

        Args:
            email (str): Email address to validate

        Returns:
            str: Validated email address

        Raises:
            ValueError: If email format is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()

    @abstractmethod
    def set_password(self) -> None:
        pass

    @abstractmethod
    def __repr__(self):
        pass


class User(BasicUser):
    """
    User class for managing user authentication and profile information in the furniture store.

    Attributes:
        name (str): User's name
        email (str): User's email address
        password (str): Hashed password
        address (str): User's delivery address
        credit (float): User's credit available to spend
        cart (ShoppingCart): User's shopping cart
        orders (List): List of user's orders
    """

    def __init__(
        self, name: str, email: str, password: str, address: str, credit: float = 0
    ):
        """
        Initialize a new User instance.
        Note: This should only be called by the Authentication class.
        """
        super().__init__(name, email, password)
        self.address = address
        self.credit = credit
        self.cart = ShoppingCart()
        self.orders = []

    def update_user_details(
        self, address: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """Update user profile information."""
        if address is None and name is None:
            return
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            basic_user_db = (
                session.query(BasicUserDB)
                .filter(BasicUserDB.email == self.email)
                .first()
            ) 

            if address is not None:
                user_db.address = address
                self.address = address
            if name is not None:
                basic_user_db.Uname = name
                self.name = name

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating user details: {e}")
        finally:
            session.close()

    def update_credit(self, credit: float) -> None:
        """Update user's credit balance."""
        try:
            session = SessionLocal()
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            user_db.credit += credit
            self.credit = user_db.credit
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating credit: {e}")
        finally:
            session.close()

    def view_cart(self) -> str:
        return str(self.cart)

    def get_order_hist(self) -> List:
        """
        Retrieve user's order history.

        Returns:
            List: List of Order objects associated with the user
        """
        return self.orders

    def set_password(self, new_password: str) -> None:
        Authentication.set_new_password(self, new_password)
        return

    def checkout(self, credit_card_num: int, coupon_code: Optional[str] = None) -> bool:
        try:
            ans = False
            if self.cart.items:
                for item, quantity in self.cart.items:
                    if not item.check_availability(quantity):
                        raise ValueError(f"There is not enough:{item} in the inventory")
            else:
                raise ValueError("There are no items in the cart")

            if coupon_code:
                discount_percent, coupon_id = self.cart.get_coupon_discount_and_id(
                    coupon_code
                )
                total_price = self.cart.apply_discount(discount_percent)
            else:
                total_price = self.cart.get_total_price()

            if self.credit:
                if self.credit <= total_price:
                    total_price -= self.credit
                    self.update_credit(self.credit * -1)
                else:
                    self.update_credit(total_price * -1)
                    total_price = 0

            if Authentication.validate_credit_card(total_price, credit_card_num):
                inv = Inventory()
                for item, amount in self.cart.items:
                    if amount < 0 or not isinstance(amount, int):
                        raise ValueError(f"item {item} has invalid quantity")
                    inv.update_amount_in_inventory(item, amount, sign=False)
            else:
                raise ValueError("Invalid Credit Card")

            new_order = Order(self.email, self.cart, coupon_id)
            self.orders.append(new_order)
            ans = True

        except Exception as e:
            print(f"Error in checkout Proc: {e}")
        finally:
            return ans

    def __repr__(self) -> str:
        """String representation of the User object."""
        return f"User: Name ={self.name}, Email={self.email}, Address={self.address}, Credit={self.credit}"


class Manager(BasicUser):

    def __init__(self, name: str, email: str, password: str):
        """
        Initialize a new User instance.
        Note: This should only be called by the Authentication class.
        """
        super().__init__(name, email, password)

    def __repr__(self) -> str:
        """String representation of the Manager object."""
        return f"Manager: Name = {self.name}, Email = {self.email}"

    def delete_user(self, email) -> None:
        """Delete user from databases."""
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == email).first()
            basic_user_db = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if user_db:
                session.delete(user_db)
            if basic_user_db:
                session.delete(basic_user_db)

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error deleting user: {e}")
        finally:
            session.close()

    def set_password(self, new_password: str) -> None:
        Authentication.set_new_password(self, new_password)
        return

    def add_manager(self, name: str, email: str, password: str) -> "Manager":
        return Authentication.create_manager(name, email, password)

    def update_order_status(self, order_id: int) -> None:
        """
        Updating order status in Database
        If already delivered raises an error
        """
        session = SessionLocal()
        try:
            order_db = session.query(OrdersDB).filter(OrdersDB.id == order_id).first()
            if order_db.id == OrderStatus.DELIVERED:
                raise ValueError(f"Order number {order_id} already delivered")
            else:
                order_db.Ostatus += 1
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating Order status: {e}")
        finally:
            session.close()

    def update_inventory(
        self, item: Union[Chair, Table], quantity: int, f_type_enum: int, sign: int
    ) -> None:
        inv = Inventory()
        try:
            if quantity < 0:
                raise ValueError("Quantity must be non-negative")
            if sign not in [0, 1]:
                raise ValueError("Sign must be 1 or 0.")
        except Exception as e:
            raise Exception(f"Error updating Inventory: {e}")
        inv.update_amount_in_inventory(item, quantity, sign)
        return

    def get_all_orders(self):
        """Retrieve all orders from the database and print them in a structured format."""
        session = SessionLocal()
        try:
            orders = session.query(OrdersDB).all()

            for order in orders:
                print("=" * 50)
                print(f"Order ID        : {order.id}")
                print(f"Status          : {order.Ostatus}")
                print(f"User Email      : {order.UserEmail}")
                print(
                    f"Coupon Code ID  : {order.idCouponsCodes if order.idCouponsCodes else 'None'}"
                )
                print("=" * 50)
                print()

        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating Order status: {e}")
        finally:

            session.close()
