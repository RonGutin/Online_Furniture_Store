import copy
from EnumsClass import OrderStatus, FurnitureType
from ShoppingCart import ShoppingCart

class Order:
    """Manages order details and status for the furniture store"""
    _order_counter = 0  # Counter to simulate unique order IDs

    def __init__(self, user_mail: int, cart: ShoppingCart):
        """Create an order from a shopping cart"""
        if not isinstance(cart, ShoppingCart):
            raise ValueError("Invalid cart. Must be an instance of ShoppingCart.")  
        Order._order_counter += 1 
        self.id = Order._order_counter
        self.user_mail = user_mail
        self.total_price = cart.get_total_price()
        self.status = OrderStatus.PENDING.value
        self.items = copy.deepcopy(cart.items)  # Performing a deep copy

    def update_status(self, new_status: OrderStatus) -> bool:
        """Update order status if valid"""
        if self.status == OrderStatus.DELIVERED.value:
            return False
        new_status = new_status.upper()
        if new_status.value in [status.name for status in OrderStatus] and self.status < new_status.value:
            self.status = new_status.value
            return True
        else:
            return False
        
    def get_status(self):
        """Returns the status name"""
        return OrderStatus.(self.status).name
        
    def __repr__(self) -> str:
        return (f"Order(id={self.id}, User email = {self.user_mail}, "
                f"Total price = {self.total_price:.2f}$, Status = {OrderStatus(self.status).name})")
