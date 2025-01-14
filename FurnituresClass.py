from abc import ABC, abstractmethod


class Furniture(ABC):
    def __init__(self, name: str, description: str, price: float, dimensions: tuple, color: str):
        self.name = name
        self.description = description
        self.price = price
        self.dimensions = dimensions
        self.color = color

    def calculate_discount(self, discount_percentage: int) -> float:
        """Calculates the price after discount."""
        if discount_percentage >= 100:
            return 0
        if discount_percentage < 0:
            raise ValueError("Discount percentage cannot be negative.")
        return self.price * (1 - 0.01 * discount_percentage)

    def apply_tax(self, tax_rate: float) -> float:
        """Calculate the price including tax."""
        if tax_rate < 0:
            raise ValueError("Tax rate cannot be negative.")
        return self.price * (1 + 0.01 * tax_rate)

    def get_color(self) -> str:
        """Return the color of the furniture."""
        return self.color

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the furniture is available in stock."""
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """Create a customized print for furniture."""
        pass


class Table(Furniture):
    def __init__(self, name: str, description: str, price: float, dimensions: tuple, color: str, material: str):
        super().__init__(name, description, price, dimensions, color)
        self.material = material

    def __repr__(self) -> str:
        return (
            f"Table Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.description}\n"
            f"  Price: ${self.price:.2f}\n"
            f"  Dimensions (L x W x H): {self.dimensions[0]} x {self.dimensions[1]} x {self.dimensions[2]} cm\n"
            f"  Material: {self.material}\n"
            f"  Color: {self.color}\n"
            f"  Here are several potential color options for this table:: {', '.join(self.available_colors)}\n"
        )

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the table is available in stock."""
        pass

    @abstractmethod
    def get_matching_chair(self) -> "Chair":
        """Abstract method to get a matching chair for the table."""
        pass


class Chair(Furniture):
    def __init__(self, name: str, description: str, price: float, dimensions: tuple, color: str, material: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(name, description, price, dimensions, color)
        self.material = material
        self.is_adjustable = is_adjustable  # האם הכיסא מתכונן
        self.has_armrest = has_armrest  # האם יש ידיות

    def __repr__(self) -> str:
        return (
            f"Chair Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.description}\n"
            f"  Is Adjustable: {'Yes' if self.is_adjustable else 'No'}\n"
            f"  Has Armrest: {'Yes' if self.has_armrest else 'No'}\n"
            f"  Price: ${self.price:.2f}\n"
            f"  Dimensions: {self.dimensions[0]} x {self.dimensions[1]} x {self.dimensions[2]} cm\n"
            f"  Material: {self.material}\n"
            f"  Color: {self.color}\n"
        )

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if the table is available in stock."""
        pass

    @abstractmethod
    def get_matching_table(self) -> Table:
        """Abstract method to get a matching chair for the table."""
        pass


class DiningTable(Table):
    def __init__(self, name: str, description: str, price: float, dimensions: tuple, color: str, material: str, available_colors: list):
        super().__init__(name, description, price, dimensions, color, material)
        self.available_colors = available_colors

    def check_availability(self) -> bool:
        """Check if the dining table is in stock."""
        return self.price > 0  # For simplicity, until we create a database!!!

    def get_matching_chair(self) -> str:
        """Find a matching chair for the dining table. """
        pass  # To be implemented later based on matching criteria.


class GamingChair(Chair):
    def __init__(self, name: str, description: str, price: float, dimensions: tuple, color: str, material: str, is_adjustable: bool, has_armrest: bool, available_colors: list):
        super().__init__(name, description, price, dimensions, color, material, is_adjustable, has_armrest)
        self.available_colors = available_colors

    def check_availability(self) -> bool:
        """Check if the dining table is in stock."""
        return self.price > 0  # For simplicity, until we create a database!!!

    def get_matching_table(self) -> Table:
        """
        Find a matching table for the gaming chair.
        Returns a Table object.
        """
        pass  # To be implemented later based on matching criteria.
