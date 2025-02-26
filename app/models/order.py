import copy
from app.models.EnumsClass import OrderStatus
from app.models.ShoppingCart import ShoppingCart
from app.data.DbConnection import (
    SessionLocal,
    OrdersDB,
    OrderContainsItemDB,
)
from typing import Optional
from app.models.inventory import Inventory


class Order:
    """Manages order details and status for the furniture store"""

    def __init__(
        self, user_mail: str, cart: ShoppingCart, coupon_id: Optional[int] = None
    ):
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")

        self.user_mail = user_mail
        self.total_price = cart.get_total_price()
        self.status = OrderStatus.PENDING.value
        self.items = copy.deepcopy(cart.items)
        self.coupon_id = coupon_id
        self.id = None

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

            inv = Inventory()
            for item, amount in self.items.items():
                order_item_db = OrderContainsItemDB(
                    OrderID=self.id,
                    ItemID=inv.get_index_furniture_by_values(item),
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
                raise ValueError("Order is already in final status (DELIVERED)")

            next_status = OrderStatus(current_status.value + 1).value

            session.query(OrdersDB).filter(OrdersDB.id == self.id).update(
                {"Ostatus": next_status}
            )
            session.commit()
            self.status = next_status
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to update order status: {e}")
        finally:
            session.close()

    def get_status(self):
        """Returns the status name"""
        return OrderStatus(self.status).name

    def __repr__(self) -> str:
        return (
            f"Order(id = {self.id}, User email = {self.user_mail}, "
            f"Total price = {self.total_price:.2f}$, Status = {OrderStatus(self.status).name})"
        )
