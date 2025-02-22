from app.data.DbConnection import SessionLocal, CouponsCodes
from typing import Tuple


class ShoppingCart:

    def __init__(self):
        self.items = (
            []
        )  # List of items, Each item looks like this: [furniture object, amount]

    def get_total_price(self):
        """Calculate the total price of all items in the cart return total price as a float"""
        return sum(item[0].get_price() * item[1] for item in self.items)

    def get_coupon_discount_and_id(self, coupon_code: str) -> Tuple[int, int]:
        discount = 0
        id_coupon = None
        session = SessionLocal()
        try:
            coupon = (
                session.query(CouponsCodes)
                .filter(CouponsCodes.CouponValue == coupon_code)
                .first()
            )
            if not coupon:
                raise ValueError("Invalid coupon code")
            else:
                discount = coupon.Discount
                id_coupon = coupon.idCouponsCodes

        except Exception as ex:
            print(f"While conecting to DB: {ex}")
        finally:
            session.close()
            return discount, id_coupon

    def apply_discount(self, Discount_percentage: int) -> float:
        """apply discount on shopping cart"""
        return sum(
            item[0].calculate_discount(Discount_percentage) * item[1]
            for item in self.items
        )

    def add_item(self, furniture, amount=1) -> bool:
        """Add a furniture item to the shopping cart."""
        ans = False
        if amount < 1 or not isinstance(amount, int):
            raise ValueError("Not the right amount")
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
                    self.items.append(
                        [furniture, amount]
                    )  # param furniture: An object of type Furniture
                    ans = True
        except Exception as ex:
            print(f"Error in adding item to shopping cart. Error: {ex}")

        if ans:
            furniture.Print_matching_product_advertisement()
        return ans

    def remove_item(self, furniture):
        """Remove a furniture item from the shopping cart."""
        is_in_items = False
        for item in self.items:
            if item[0] == furniture:
                self.items.remove(item)
                is_in_items = True
        if not is_in_items:
            raise ValueError("Item not in cart - nothing to remove")

    def __repr__(self):
        """Return a string representation of the shopping cart."""
        if not self.items:
            return "Shopping cart is empty."
        lines = ["Shopping Cart:"]
        for i, (furniture, amount) in enumerate(self.items, start=1):
            lines.append(f"{i}. {repr(furniture)}\n   Quantity: {amount}")
        return "\n".join(lines)
