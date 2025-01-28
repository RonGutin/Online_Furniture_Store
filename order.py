from EnumsClass import OrderStatus, FurnitureType
from ShoppingCart import ShoppingCart

class OrderItem:
    """Represents an item in an order"""
    def __init__(self, furniture_type: int, furniture_id: str, price: float, quantity: int = 1):
        self.furniture_type = furniture_type
        self.furniture_id = furniture_id
        self.price = price
        self.quantity = quantity

class Order:
    """Manages order details and status for the furniture store"""
    _order_counter = 1  # Counter to simulate unique order IDs

    def __init__(self, user_id: int, cart: ShoppingCart):
        """Create an order from a shopping cart"""
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")
        
        self.id = Order._order_counter
        Order._order_counter += 1 

        self.user_id = user_id
        self.total_price = cart.get_total_price()
        self.status = OrderStatus.PENDING.value
        self.items = [
            OrderItem(
                furniture_type=FurnitureType[item.__class__.__name__.upper()].value,
                furniture_id=item.name,
                price=item.price
            ) for item in cart.items
        ]

    def update_status(self, new_status: OrderStatus) -> bool:
        """Update order status if valid"""
        if self.status == OrderStatus.DELIVERED.value:
            return False
        self.status = new_status.value
        return True

    def __repr__(self) -> str:
        return (f"Order(id={self.id}, user_id={self.user_id}, "
                f"total_price=${self.total_price:.2f}, status={OrderStatus(self.status).name})")
