from app.data.DbConnection import SessionLocal, CouponsCodes
from app.models.FurnituresClass import DiningTable, GamingChair
from app.models.ShoppingCart import ShoppingCart
from app.api.endpoints import app

"""
Important - this file is temporary until we build a real main file
"""


def main():
    dining_table = DiningTable(
        # name="Elegant Dining Table",
        # description="A spacious dining table made from premium oak wood.",
        # price=500.00,
        # dimensions=(200, 100, 75),
        color="Brown",
        material="Wood",
    )

    gaming_chair = GamingChair(
        # name="Pro Gamer Chair",
        # description="An ergonomic gaming chair with adjustable height and armrests.",
        # price=175.00,
        # dimensions=(50, 50, 120),
        color="Black",
        is_adjustable=True,
        has_armrest=True,
    )

    def seed_coupons():
        session = SessionLocal()
        try:
            coupons = [
                CouponsCodes(CouponValue="DISCOUNT10", Discount=10),
                CouponsCodes(CouponValue="SAVE20", Discount=20),
            ]
            session.add_all(coupons)
            session.commit()
        finally:
            session.close()

    # seed_coupons()

    print("=== Testing DiningTable ===")
    print(dining_table)
    print(
        f"Is the table available in stock? "
        f"{'Yes' if dining_table.check_availability() else 'No'}"
    )
    print("=== Prices after discount ===")
    for discount in [0, 10, 50, 100]:
        print(f"Discount {discount}%: ${dining_table.calculate_discount(discount):.2f}")
    print(f"Price including 15% tax: ${dining_table.apply_tax(15):.2f}")

    print("\n=== Testing GamingChair ===")
    print(gaming_chair)
    print(
        f"Is the chair available in stock? "
        f"{'Yes' if gaming_chair.check_availability() else 'No'}"
    )
    print("=== Prices after discount ===")
    for discount in [0, 10, 50, 100]:
        print(f"Discount {discount}%: ${gaming_chair.calculate_discount(discount):.2f}")
    print(f"Price including 18% tax: ${gaming_chair.apply_tax(18):.2f}")

    # Creating a shopping cart example
    print("\n=== Creating a shopping cart ===")
    cart = ShoppingCart()
    cart.add_item(dining_table)
    cart.add_item(gaming_chair)

    print("\nCart content:")
    print(cart)

    print("\nTotal price of all items in the cart: ")
    print(f"${cart.get_total_price():.2f}")

    print("\n=== Applying coupons ===")
    # try:
    #     final_price = cart.apply_discount("SAVE20")
    #     print(f"Price after applying SAVE20 coupon: ${final_price:.2f}")
    # except ValueError as e:
    #     print(e)

    # print("\n=== Removing an item ===")
    # cart.remove_item(dining_table)
    # print(cart)

    # print("\n=== Removing an item not in the cart ===")
    try:
        cart.remove_item(dining_table)
    except ValueError as e:
        print(e)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)