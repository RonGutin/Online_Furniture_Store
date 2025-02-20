import unittest
import io
from unittest.mock import patch, MagicMock
from app.models.ShoppingCart import ShoppingCart
from app.models.FurnituresClass import DiningTable, GamingChair


class TestShoppingCart(unittest.TestCase):
    def setUp(self):
        self.cart = ShoppingCart()
        self.dining_table = DiningTable(color="brown", material="wood")
        self.gaming_chair = GamingChair(
            color="Black", is_adjustable=True, has_armrest=True
        )
        self.dining_table.price = 1000.0
        self.gaming_chair.price = 500.0

    def test_get_total_price_empty_cart(self):
        self.assertEqual(self.cart.get_total_price(), 0)

    def test_get_total_price_with_items(self):
        self.dining_table.check_availability = MagicMock(return_value=True)
        self.gaming_chair.check_availability = MagicMock(return_value=True)
        self.cart.add_item(self.dining_table, amount=2)
        self.cart.add_item(self.gaming_chair, amount=1)
        self.assertEqual(self.cart.get_total_price(), 2 * 1000 + 1 * 500)

    @patch("app.models.ShoppingCart.SessionLocal")
    def test_get_coupon_discount_and_id_valid(self, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query

        mock_coupon = MagicMock()
        mock_coupon.CouponValue = "SAVE10"
        mock_coupon.Discount = 10
        mock_coupon.idCouponsCodes = 1
        mock_query.filter.return_value.first.return_value = mock_coupon

        discount, coupon_id = self.cart.get_coupon_discount_and_id("SAVE10")
        self.assertEqual(discount, 10)
        self.assertEqual(coupon_id, 1)

    @patch("app.models.ShoppingCart.SessionLocal")
    def test_get_coupon_discount_and_id_invalid(self, mock_session_local):
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        discount, coupon_id = self.cart.get_coupon_discount_and_id("FAKECODE")
        self.assertEqual(discount, 0)
        self.assertIsNone(coupon_id)

    def test_apply_discount_empty_cart(self):
        self.assertEqual(self.cart.apply_discount(10), 0)

    def test_apply_discount_with_items(self):
        self.dining_table.check_availability = MagicMock(return_value=True)
        self.cart.add_item(self.dining_table, amount=2)
        # Each table costs 1000, 10% discount => 900 per table => total 1800
        self.assertEqual(self.cart.apply_discount(10), 1800.0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_add_item_valid_and_ad_print(self, mock_stdout):
        self.dining_table.check_availability = MagicMock(return_value=True)
        result = self.cart.add_item(self.dining_table, amount=2)
        self.assertTrue(result)
        self.assertEqual(len(self.cart.items), 1)
        self.assertIn("SPECIAL OFFER", mock_stdout.getvalue())

    def test_add_item_invalid_amount(self):
        with self.assertRaises(ValueError):
            self.cart.add_item(self.dining_table, amount=0)
        with self.assertRaises(ValueError):
            self.cart.add_item(self.dining_table, amount=-1)
        with self.assertRaises(ValueError):
            self.cart.add_item(self.dining_table, amount=1.5)

    def test_add_item_not_available(self):
        self.dining_table.check_availability = MagicMock(return_value=False)
        result = self.cart.add_item(self.dining_table, amount=1)
        self.assertFalse(result)
        self.assertEqual(len(self.cart.items), 0)

    def test_remove_item_valid(self):
        self.dining_table.check_availability = MagicMock(return_value=True)
        self.cart.add_item(self.dining_table, amount=1)
        self.cart.remove_item(self.dining_table)
        self.assertEqual(len(self.cart.items), 0)

    def test_remove_item_not_in_cart(self):
        with self.assertRaises(ValueError):
            self.cart.remove_item(self.gaming_chair)

    def test_repr_empty_cart(self):
        self.assertEqual(repr(self.cart), "Shopping cart is empty.")

    def test_repr_non_empty_cart(self):
        self.dining_table.check_availability = MagicMock(return_value=True)
        self.cart.add_item(self.dining_table, amount=1)
        cart_repr = repr(self.cart)
        self.assertIn("Shopping Cart:", cart_repr)
        self.assertIn("Table Details:", cart_repr)


if __name__ == "__main__":
    unittest.main()
