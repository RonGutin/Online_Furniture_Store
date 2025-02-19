import unittest
from app.models.FurnituresClass import (
    DiningTable, WorkDesk, CoffeeTable, 
    GamingChair, WorkChair
)

class TestFurniture(unittest.TestCase):

    def setUp(self):
        self.dining_table = DiningTable(color="brown", material="wood")
        self.work_desk = WorkDesk(color="black", material="wood")
        self.coffee_table = CoffeeTable(color="gray", material="glass")
        self.gaming_chair = GamingChair(color="black", is_adjustable=True, has_armrest=True)
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


if __name__ == "__main__":
    unittest.main()
