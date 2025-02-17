import copy
from EnumsClass import OrderStatus, FurnitureType
from ShoppingCart import ShoppingCart
from app.data.DbConnection import SessionLocal, OrdersDB, OrderContainsItemDB , InventoryDB
from typing import Optional

class Order:
    """Manages order details and status for the furniture store"""

    def __init__(self, user_mail: str, cart: ShoppingCart, coupon_id: Optional[int] = None):
        """Create an order from a shopping cart"""
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")  
        self.user_mail = user_mail
        self.total_price = cart.get_total_price()
        self.status = OrderStatus.PENDING.value
        self.items = copy.deepcopy(cart.items)  # Performing a deep copy
        session = SessionLocal()
        try:
            orders_db = OrdersDB(
                Ostatus = self.status,
                UserEmail = user_mail,
                idCouponsCodes = coupon_id
            )
            session.add(orders_db)
            session.commit()
            session.refresh(orders_db) 
            self.id = orders_db.id 

            for item, amount in cart.items:
                order_contains_item_db = OrderContainsItemDB(
                    Orderid = self.id,
                    ItemID = session.query(InventoryDB.id).filter(
                                    and_(
                                        InventoryDB.furniture_type == f_type_enum,
                                        InventoryDB.color == item.color,
                                        InventoryDB.high == item.dimensions[0],
                                        InventoryDB.depth == item.dimensions[1],
                                        InventoryDB.width == item.dimensions[2],
                                        InventoryDB.material == item.material
                                    )
                                ).first()
                )


            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating Order status: {e}")
        finally:
            session.close()  

    def update_status(self) -> None:
        """
        Updates the order status to the next status in the enum sequence.
        
        Raises:
            ValueError: If the order is already in its final status (DELIVERED)
        """
        current_status = OrderStatus(self.status)
        
        # Check if we're already at the final status
        if current_status == OrderStatus.DELIVERED:
            raise ValueError("Order is already in final status (DELIVERED)")
        
        # Move to next status
        self.status = OrderStatus(self.status + 1).value
        
    def get_status(self):
        """Returns the status name"""
        return OrderStatus(self.status).name
        
    def __repr__(self) -> str:
        return (f"Order(id = {self.id}, User email = {self.user_mail}, "
                f"Total price = {self.total_price:.2f}$, Status = {OrderStatus(self.status).name})")
