from DbConnection import SessionLocal, CouponsCodes


class ShoppingCart:
    def __init__(self, user=None):
        # param user: None for guest users, or a User object for registered users.
        self.items = []  # List of furniture objects
        self.user = user  # None if user is a guest, otherwise User object

    def get_total_price(self):  # Calculate the total price of all items in the cart return total price as a float.
        return sum(item.price for item in self.items)
     
    def apply_discount(self, coupon_code):
        session = SessionLocal()
        try:
            coupon = session.query(CouponsCodes).filter(CouponsCodes.CouponValue == coupon_code).first()
            if not coupon:
                raise ValueError("Invalid coupon code")
            total_price = self.get_total_price()
            discount_amount = total_price * (coupon.Discount / 100)
            return total_price - discount_amount
        except Exception as ex:
            print(f"While coneccting to DB: {ex}")
        finally:
            session.close()
            
    def add_item(self, furniture):  # Add a furniture item to the shopping cart.
        self.items.append(furniture) # param furniture: An object of type Furniture

    def remove_item(self, furniture):  # Remove a furniture item from the shopping cart.
        if furniture in self.items: # param furniture: An object of type Furniture to remove.

            self.items.remove(furniture)
        else:
            raise ValueError("Item not in cart")

    def __repr__(self):  # Return a string representation of the shopping cart.

        if not self.items:
            return "Shopping cart is empty."
        
        item_descriptions = [f"{item.name} - ${item.price} | Dimensions: {item.dimensions} | Color: {item.color}\nDescription: {item.description}"
            for item in self.items]
        return f"Shopping Cart:\n" + "\n".join(item_descriptions)  # return: String describing the shopping cart contents.
