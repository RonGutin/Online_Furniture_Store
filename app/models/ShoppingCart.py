from app.data.DbConnection import SessionLocal, CouponsCodes


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
            
    def add_item(self, furniture, amount = 1) -> bool:  # Add a furniture item to the shopping cart.
        ans = False
        if amount < 1:
            return ans
        try:
            is_in_items = False
            index_item = -1
            for i in range(len(self.items)):
                if furniture == self.items[i][0]:
                    is_in_items = True
                    index_item = i
            if is_in_items:
                if furniture.check_availability(amount):
                    self.items[index_item][1] = amount 
                    ans = True  
            else:
                if furniture.check_availability(amount):
                    self.items.append([furniture, amount]) # param furniture: An object of type Furniture
                    ans = True
        except Exception as ex:
            print(f"Error in adding item to shopping cart. Error: {ex}") 
        return ans


    def remove_item(self, furniture):  # Remove a furniture item from the shopping cart.
        is_in_items = False
        for item in self.items:
            if item[0] == furniture:
                self.items.remove(item)
                is_in_items = True
        if not is_in_items:
            raise ValueError("Item not in cart - nothing to remove")

    def __repr__(self):  # Return a string representation of the shopping cart.

        if not self.items:
            return "Shopping cart is empty."
        
        item_descriptions = [f"{item.name} - ${item.price} | Dimensions: {item.dimensions} | Color: {item.color}\nDescription: {item.description}"
            for item in self.items]
        return f"Shopping Cart:\n" + "\n".join(item_descriptions)  # return: String describing the shopping cart contents.
