import unittest
from app.models.FurnituresClass import DiningTable, WorkDesk, CoffeeTable, GamingChair, WorkChair

class TestFurnitures(unittest.TestCase):
    
    def setUp(self):
        self.dining_table = DiningTable("Dining Table", "Wooden dining table", 1500.0, "Brown", "Wood")
        self.work_desk = WorkDesk("Office Desk", "Work desk with drawers", 2000.0, "White", "Wood")
        self.coffee_table = CoffeeTable("Coffee Table", "Glass coffee table", 500.0, "Gray", "Glass")
        self.gaming_chair = GamingChair("Gaming Chair", "Ergonomic gaming chair", 1000.0, "Black", True, True)
        self.work_chair = WorkChair("Work Chair", "Office chair with wheels", 800.0, "Red", True, False)

    def test_create_valid_furniture(self):
        self.assertIsInstance(self.dining_table, DiningTable)
        self.assertIsInstance(self.work_desk, WorkDesk)
        self.assertIsInstance(self.coffee_table, CoffeeTable)
        self.assertIsInstance(self.gaming_chair, GamingChair)
        self.assertIsInstance(self.work_chair, WorkChair)

    def test_invalid_color(self):
        with self.assertRaises(ValueError):
            DiningTable("Table", "Invalid color", 1000.0, "Purple", "Wood")  
        with self.assertRaises(ValueError):
            WorkDesk("Desk", "Invalid color", 1500.0, "Green", "Wood") 
    def test_invalid_material(self):
        with self.assertRaises(ValueError):
            DiningTable("Table", "Invalid material", 1000.0, "Brown", "Plastic") 
        with self.assertRaises(ValueError):
            CoffeeTable("Table", "Invalid material", 800.0, "Gray", "Wood")  

    def test_calculate_discount(self):
        self.assertEqual(self.dining_table.calculate_discount(10), 1350.0)
        self.assertEqual(self.gaming_chair.calculate_discount(50), 500.0)
        with self.assertRaises(ValueError):
            self.work_desk.calculate_discount(-5)  

    def test_apply_tax(self):
        self.assertAlmostEqual(self.work_desk.apply_tax(10), 2200.0)
        self.assertAlmostEqual(self.coffee_table.apply_tax(15), 575.0)
        with self.assertRaises(ValueError):
            self.work_chair.apply_tax(-8)  

    def test_check_availability(self):
        self.assertTrue(self.dining_table.check_availability())
        self.assertFalse(DiningTable("Cheap Table", "Table with zero price", 0.0, (120, 80, 75), "Brown", "Wood").check_availability())

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            DiningTable("Invalid", "Invalid dimensions", 1000.0, "Brown", "Wood")
        with self.assertRaises(ValueError):
            CoffeeTable("Invalid", "Negative price", -200.0, "Gray", "Glass")

if __name__ == "__main__":
    unittest.main()
    
