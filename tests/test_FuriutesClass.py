import unittest
import io
from unittest.mock import patch
from app.models.FurnituresClass import (
    DiningTable,
    WorkDesk,
    CoffeeTable,
    GamingChair,
    WorkChair,
)


class TestFurniture(unittest.TestCase):
    def setUp(self):
        self.dining_table = DiningTable(color="brown", material="wood")
        self.work_desk = WorkDesk(color="black", material="wood")
        self.coffee_table = CoffeeTable(color="gray", material="glass")
        self.gaming_chair = GamingChair(
            color="black", is_adjustable=True, has_armrest=True
        )
        self.work_chair = WorkChair(color="red", is_adjustable=True, has_armrest=False)

    def test_valid_furniture_creation(self):
        self.assertIsInstance(self.dining_table, DiningTable)
        self.assertIsInstance(self.work_desk, WorkDesk)
        self.assertIsInstance(self.coffee_table, CoffeeTable)
        self.assertIsInstance(self.gaming_chair, GamingChair)
        self.assertIsInstance(self.work_chair, WorkChair)

    def test_invalid_color(self):
        with self.assertRaises(ValueError):
            DiningTable(color="Purple", material="wood")
        with self.assertRaises(ValueError):
            WorkDesk(color="Green", material="wood")

    def test_invalid_material(self):
        with self.assertRaises(ValueError):
            DiningTable(color="brown", material="Plastic")
        with self.assertRaises(ValueError):
            CoffeeTable(color="gray", material="Wood")

    def test_calculate_discount(self):
        self.dining_table.price = 1000.0
        self.assertEqual(self.dining_table.calculate_discount(10), 900.0)
        self.assertEqual(self.dining_table.calculate_discount(100), 0.0)
        with self.assertRaises(ValueError):
            self.dining_table.calculate_discount(-5)

    def test_apply_tax(self):
        self.dining_table.price = 1000.0
        self.assertAlmostEqual(self.dining_table.apply_tax(10), 1100.0)
        with self.assertRaises(ValueError):
            self.dining_table.apply_tax(-8)

    def test_check_availability(self):
        ans = self.dining_table.check_availability(amount=1)
        self.assertIsInstance(ans, bool)
        ans_chair = self.gaming_chair.check_availability(amount=2)
        self.assertIsInstance(ans_chair, bool)

    def test_get_color(self):
        self.assertEqual(self.dining_table.get_color(), "brown")
        self.assertEqual(self.work_desk.get_color(), "black")
        self.assertEqual(self.gaming_chair.get_color(), "black")

    def test_get_price(self):
        self.dining_table.price = 1500.0
        self.assertEqual(self.dining_table.get_price(), 1500.0)
        self.dining_table.price = None
        with self.assertRaises(ValueError):
            self.dining_table.get_price()

    def test_print_matching_product_advertisement_table(self):
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            self.dining_table.Print_matching_product_advertisement()
            output = fake_out.getvalue()
            self.assertIn("SPECIAL OFFER", output)

    def test_print_matching_product_advertisement_chair(self):
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            self.gaming_chair.Print_matching_product_advertisement()
            output = fake_out.getvalue()
            self.assertIn("SPECIAL OFFER", output)


if __name__ == "__main__":
    unittest.main()
