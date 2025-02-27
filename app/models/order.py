from copy import deepcopy
from typing import Optional

from app.data.DbConnection import OrdersDB, OrderContainsItemDB, SessionLocal
from app.models.EnumsClass import OrderStatus
from app.models.ShoppingCart import ShoppingCart
from app.utils import get_index_furniture_by_values


class Order:
    """Represents an order in the furniture store."""

    def __init__(
        self, user_mail: str, cart: ShoppingCart, coupon_id: Optional[int] = None
    ) -> None:
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")

        self._user_mail: str = user_mail
        self._total_price: float = cart.get_total_price()
        self._status: str = OrderStatus.PENDING.value
        self._items: list = deepcopy(cart.items)
        self._coupon_id: Optional[int] = coupon_id
        self._id: Optional[int] = None

        self._save_to_db()

    def get_user_mail(self) -> str:
        return self._user_mail

    def set_user_mail(self, user_mail: str) -> None:
        self._user_mail = user_mail

    def get_total_price(self) -> float:
        return self._total_price

    def set_total_price(self, total_price: float) -> None:
        self._total_price = total_price

    def get_status(self) -> str:
        return OrderStatus(self._status).name

    def set_status(self, status: str = OrderStatus.PENDING) -> None:
        self._status = status

    def get_items(self) -> list:
        return self._items

    def set_items(self, items: list) -> None:
        self._items = items

    def get_coupon_id(self) -> Optional[int]:
        return self._coupon_id

    def set_coupon_id(self, coupon_id: Optional[int]) -> None:
        self._coupon_id = coupon_id

    def get_id(self) -> Optional[int]:
        return self._id

    def set_id(self, order_id: Optional[int]) -> None:
        self._id = order_id

    def _save_to_db(self) -> None:
        session = SessionLocal()
        try:
            order_db = OrdersDB(
                Ostatus=self._status,
                UserEmail=self._user_mail,
                idCouponsCodes=self._coupon_id,
            )
            session.add(order_db)
            session.commit()
            session.refresh(order_db)
            self._id = order_db.id

            for item, amount in self._items.items():
                order_item_db = OrderContainsItemDB(
                    OrderID=self._id,
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
        session = SessionLocal()
        try:
            current_status = OrderStatus(self._status)

            if current_status == OrderStatus.DELIVERED:
                raise ValueError("Order is already in final status (DELIVERED)")

            next_status = OrderStatus(current_status.value + 1).value

            session.query(OrdersDB).filter(OrdersDB.id == self._id).update(
                {"Ostatus": next_status}
            )
            session.commit()
            self._status = next_status

        except ValueError:
            raise ValueError("Order is already in final status (DELIVERED)")

        except Exception:
            session.rollback()

        finally:
            session.close()

    def __repr__(self) -> str:
        return (
            f"Order(id = {self._id}, User email = {self._user_mail}, "
            f"Total price = {self._total_price:.2f}$, Status = {OrderStatus(self._status).name})"
        )
