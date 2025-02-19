import unittest
from app.models.FurnitureFactory import FurnitureFactory
from app.models.FurnituresClass import DiningTable, WorkDesk, CoffeeTable, WorkChair, GamingChair

class TestFurnitureFactory(unittest.TestCase):
    def setUp(self):
        self.factory = FurnitureFactory()

    def test_create_dining_table(self):
        table = self.factory.create_furniture(
            "DINING_TABLE",
            color="brown",
            material="wood"
        )
        self.assertIsInstance(table, DiningTable)
        self.assertEqual(table.color, "brown")
        self.assertEqual(table.material, "wood")

    def test_create_work_desk(self):
        desk = self.factory.create_furniture(
            "WORK_DESK",
            color="white",
            material="glass"
        )
        self.assertIsInstance(desk, WorkDesk)
        self.assertEqual(desk.color, "white")
        self.assertEqual(desk.material, "glass")

    def test_create_coffee_table(self):
        coffee_table = self.factory.create_furniture(
            "COFFEE_TABLE",
            color="gray",
            material="plastic"
        )
        self.assertIsInstance(coffee_table, CoffeeTable)
        self.assertEqual(coffee_table.color, "gray")
        self.assertEqual(coffee_table.material, "plastic")

    def test_create_work_chair(self):
        work_chair = self.factory.create_furniture(
            "WORK_CHAIR",
            color="red",
            is_adjustable=True,
            has_armrest=False
        )
        self.assertIsInstance(work_chair, WorkChair)
        self.assertEqual(work_chair.color, "red")
        self.assertTrue(work_chair.is_adjustable)
        self.assertFalse(work_chair.has_armrest)

    def test_create_gaming_chair(self):
        gaming_chair = self.factory.create_furniture(
            "GAMING_CHAIR",
            color="black",
            is_adjustable=True,
            has_armrest=True
        )
        self.assertIsInstance(gaming_chair, GamingChair)
        self.assertEqual(gaming_chair.color, "black")
        self.assertTrue(gaming_chair.is_adjustable)
        self.assertTrue(gaming_chair.has_armrest)

    def test_invalid_furniture_type(self):
        with self.assertRaises(ValueError):
            self.factory.create_furniture(
                "SOFA",
                color="brown",
                material="wood"
            )

    def test_missing_parameter_for_table(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture(
                "DINING_TABLE",
                color="brown"
            )

    def test_missing_parameter_for_chair(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture(
                "WORK_CHAIR",
                color="black",
                is_adjustable=True
            )

    def test_invalid_color_type(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture(
                "COFFEE_TABLE",
                color=123,
                material="glass"
            )

    def test_invalid_material_type(self):
        with self.assertRaises(TypeError):
            self.factory.create_furniture(
                "WORK_DESK",
                color="black",
                material=None
            )

if __name__ == "__main__":
    unittest.main()
