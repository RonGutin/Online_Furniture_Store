from copy import deepcopy

from typing import Optional

from app.data.DbConnection import OrdersDB, OrderContainsItemDB, SessionLocal
from app.models.EnumsClass import OrderStatus
from app.models.ShoppingCart import ShoppingCart
from app.utils import get_index_furniture_by_values


class Order:
    """Represents an order in the furniture store.

    Attributes:
        user_mail (str): The email of the user placing the order.
        total_price (float): The total price of the items in the order.
        status (str): The current status of the order.
        items (list): A deep copy of the items in the shopping cart.
        coupon_id (Optional[int]): The ID of the applied coupon (if any).
        id (Optional[int]): The ID of the order in the database.
    """

    def __init__(
        self, user_mail: str, cart: ShoppingCart, coupon_id: Optional[int] = None
    ) -> None:
        """
        Initializes an order with user details, cart contents, and optional coupon.

        Args:
            user_mail (str): The email of the user placing the order.
            cart (ShoppingCart): The shopping cart associated with the order.
            coupon_id (Optional[int], optional): The ID of the applied coupon. Defaults to None.

        Raises:
            ValueError: If the provided cart is not an instance of ShoppingCart.
        """
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")

        self.user_mail: str = user_mail
        self.total_price: float = cart.get_total_price()
        self.status: str = OrderStatus.PENDING.value
        self.items: list = deepcopy(cart.items)
        self.coupon_id: Optional[int] = coupon_id
        self.id: Optional[int] = None

        self._save_to_db()

    def _save_to_db(self) -> None:
        """Saves the order to the database"""
        session = SessionLocal()
        try:
            order_db = OrdersDB(
                Ostatus=self.status,
                UserEmail=self.user_mail,
                idCouponsCodes=self.coupon_id,
            )
            session.add(order_db)
            session.commit()
            session.refresh(order_db)
            self.id = order_db.id

            for item, amount in self.items.items():
                order_item_db = OrderContainsItemDB(
                    OrderID=self.id,
                    ItemID=get_index_furniture_by_values(item),
                    Amount=amount,
                )
                session.add(order_item_db)

            session.commit()

        except Exception as e:
            session.rollback()
            raise Exception(f"Error saving order to database: {e}")

        finally:
            session.close()

    def update_status(self) -> None:
        """
        Updates the order status to the next status in the enum sequence.

        Raises:
            ValueError: If the order is already in its final status (DELIVERED)
        """
        session = SessionLocal()
        try:
            current_status = OrderStatus(self.status)

            if current_status == OrderStatus.DELIVERED:
                raise ValueError

            next_status = OrderStatus(current_status.value + 1).value

            session.query(OrdersDB).filter(OrdersDB.id == self.id).update(
                {"Ostatus": next_status}
            )
            session.commit()
            self.status = next_status

        except ValueError:
            raise ValueError("Order is already in final status (DELIVERED)")

        except Exception:
            session.rollback()

        finally:
            session.close()

    def get_status(self) -> str:
        """Returns the order status as a string."""
        return OrderStatus(self.status).name

    def __repr__(self) -> str:
        """Returns a string representation of the order."""
        return (
            f"Order(id = {self.id}, User email = {self.user_mail}, "
            f"Total price = {self.total_price:.2f}$, Status = {OrderStatus(self.status).name})"
        )
