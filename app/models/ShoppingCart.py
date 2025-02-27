from typing import Tuple, Optional
from app.data.DbConnection import SessionLocal, CouponsCodes
from app.models.FurnituresClass import Furniture


class ShoppingCart:
    """
    Represents a shopping cart for a user.

    Attributes:
        items (list): List of items in the cart. Each item is represented as a
        list: [furniture object, amount].
    """

    def __init__(self):
        """
        Initialize an empty shopping cart.
        """
        self.items = []  # List of items, Each item looks like this:
        # [furniture object, amount]

    def get_total_price(self) -> float:
        """Calculate the total price of all items in the cart and return it."""
        return sum(item[0].get_price() * item[1] for item in self.items)

    def get_coupon_discount_and_id(self, coupon_code: str) -> Tuple[int, Optional[int]]:
        """
        Retrieve the discount and ID for a given coupon code.

        Args:
            coupon_code (str): The coupon code to search for.

        Returns:
            Tuple[int, Optional[int]]: A tuple containing the discount (int)
            and coupon ID (int or None if not found).
        """

        discount: int = 0
        id_coupon: Optional[int] = None

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
            print(f"While connecting to DB: {ex}")

        finally:
            session.close()
            return discount, id_coupon

    def apply_discount(self, Discount_percentage: int) -> float:
        """Apply a discount on the shopping cart for all items."""
        return sum(
            item[0].calculate_discount(Discount_percentage) * item[1]
            for item in self.items
        )

    def add_item(self, furniture: "Furniture", amount: int = 1) -> bool:
        """
        Add a furniture item to the shopping cart.

        Args:
            furniture (Furniture): The furniture item to add to the cart.
            amount (int, optional): The quantity of the item to add.
                Defaults to 1.

        Returns:
            bool: True if the item was successfully added or updated in the cart,
                False otherwise.
        """

        # Validate the amount
        if amount < 1 or not isinstance(amount, int):
            raise ValueError("Not the right amount")

        ans: bool = False
        try:
            is_in_items: bool = False
            index_item: int = -1

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

    def remove_item(self, furniture: "Furniture") -> None:
        """
        Remove a furniture item from the shopping cart.

        Args:
            furniture (Furniture): The furniture item to remove from the cart.

        Raises:
            ValueError: If the furniture item is not in the cart.
        """

        is_in_items: bool = False

        # Iterate through the cart items to find the furniture to remove
        for item in self.items:
            if item[0] == furniture:
                self.items.remove(item)
                is_in_items = True
                break  # Exit the loop once the item is found and removed

        # If the item wasn't found in the cart, raise an exception
        if not is_in_items:
            raise ValueError("Item not in cart - nothing to remove")

    def __repr__(self) -> str:
        """Return a string representation of the shopping cart."""

        if not self.items:
            return "Shopping cart is empty."

        lines: list[str] = ["Shopping Cart:"]

        for i, (furniture, amount) in enumerate(self.items, start=1):
            lines.append(f"{i}. {repr(furniture)}\n   Quantity: {amount}")

        return "\n".join(lines)
