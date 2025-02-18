import unittest
from app.models.FurnitureFactory import FurnitureFactory
from app.models.FurnituresClass import DiningTable, WorkDesk, CoffeeTable, WorkChair, GamingChair

class TestFurnitureFactory(unittest.TestCase):
    def setUp(self):
        self.factory = FurnitureFactory()

    def test_create_dining_table(self):
        furniture = self.factory.create_furniture("DINING_TABLE", name="Table", description="Wooden table",
                                                  price=1200.0, dimensions=(120, 80, 75), color="Brown", material="Wood")
        self.assertIsInstance(furniture, DiningTable)

    def test_create_work_desk(self):
        furniture = self.factory.create_furniture("WORK_DESK", name="Desk", description="Work desk",
                                                  price=1500.0, dimensions=(150, 75, 70), color="White", material="wood")
        self.assertIsInstance(furniture, WorkDesk)

    def test_create_coffee_table(self):
        furniture = self.factory.create_furniture("COFFEE_TABLE", name="Coffee Table", description="Glass table",
                                                  price=800.0, dimensions=(90, 60, 45), color="Gray", material="Glass")
        self.assertIsInstance(furniture, CoffeeTable)

    def test_create_work_chair(self):
        furniture = self.factory.create_furniture("WORK_CHAIR", name="Work Chair", description="Office chair",
                                                  price=1000.0, dimensions=(65, 65, 110), color="Red", is_adjustable=True, has_armrest=True)
        self.assertIsInstance(furniture, WorkChair)

    def test_create_gaming_chair(self):
        furniture = self.factory.create_furniture("GAMING_CHAIR", name="Gaming Chair", description="Ergonomic chair",
                                                  price=900.0, dimensions=(70, 70, 130), color="Black", is_adjustable=True, has_armrest=True)
        self.assertIsInstance(furniture, GamingChair)

    def test_invalid_furniture_type(self):
        with self.assertRaises(ValueError):
            self.factory.create_furniture("SOFA", name="Sofa", description="Comfy sofa", price=500, dimensions=(200, 80, 90), color="Blue")

    def test_missing_parameter(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture("DINING_TABLE", name="Table", description="Wooden table", price=1000.0)

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            self.factory.create_furniture("COFFEE_TABLE", name="Coffee Table", description="Glass table", price=-100.0,
                                          dimensions=(90, 60, 45), color="Gray", material="Glass")

    def test_negative_dimensions(self):
        with self.assertRaises(ValueError):
            self.factory.create_furniture("WORK_DESK", name="Desk", description="Work desk", price=1500.0,
                                          dimensions=(-150, 75, 70), color="White", material="Metal")

    def test_invalid_color_type(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture("GAMING_CHAIR", name="Gaming Chair", description="Ergonomic chair",
                                          price=900.0, dimensions=(70, 70, 130), color=123, is_adjustable=True, has_armrest=True)

if __name__ == "__main__":
    unittest.main()