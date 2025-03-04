from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.data.DbConnection import SessionLocal, InventoryDB
from app.utils import get_index_furniture_by_values


class Furniture(ABC):
    """
    A base class for furniture, providing common
    attributes and methods for different types of furniture.

    Attributes:
        color (str): The color of the furniture item.
        price (float): The price of the furniture item.
        name (str): The name of the furniture item.
        desc (str): A description of the furniture item.
    """

    def __init__(self, color: str):
        """
        Initializes a Furniture object with a specific color and retrieves additional details.

        Args:
            color (str): The color of the furniture item.

        Raises:
            ValueError: If the color is invalid.
        """
        self._validate_color(color)  # Checking that the color matches
        self.color = color
        price, name, desc = self._get_info_furniture_by_key()
        self._price = price
        self.name = name
        self.desc = desc

    def _validate_color(self, color: str) -> None:
        """
        Validates that the provided color is a valid option.

        Checks if the color is a string and if it matches one of the available colors
        defined in the class (if applicable).

        Args:
            color (str): The color to be validated.

        Raises:
            TypeError: If the color is not a string.
            ValueError: If the color is not allowed based on the available colors.
        """
        # Ensure the color is a string
        if not isinstance(color, str):
            raise TypeError("Color must be a string.")

        # Check if available_colors is defined and if the color is valid
        if (
            hasattr(self.__class__, "available_colors")
            and self.__class__.available_colors is not None
        ):
            allowed = [c.lower() for c in self.__class__.available_colors]
            if color.lower() not in allowed:
                raise ValueError(
                    f"Color '{color}' is not allowed. Allowed colors: "
                    f"{', '.join(self.__class__.available_colors)}"
                )

    def calculate_discount(self, discount_percentage: int) -> float:
        """
        Calculates the price after applying the given discount percentage.

        Args:
            discount_percentage (int): The discount percentage to be applied (0-100).

        Returns:
            float: The price after the discount is applied.

        Raises:
            ValueError: If the discount percentage is negative.
        """
        if not isinstance(discount_percentage, (int, float)):
            raise TypeError(
                "discount_percentage must be an integer or float between 0 and 100"
            )
        if discount_percentage < 0 or discount_percentage > 100:
            raise ValueError(
                "discount_percentage must be an integer or float between 0 and 100"
            )
        if discount_percentage >= 100:
            return 0

        return self._price * (1 - 0.01 * discount_percentage)

    def apply_tax(self, tax_rate: float) -> None:
        """
        Calculates the price including the given tax rate.

        Args:
            tax_rate (float): The tax rate to be applied (must be non-negative).

        Returns:
            float: The price including tax.

        Raises:
            ValueError: If the tax rate is negative.
        """
        if tax_rate < 0:
            raise ValueError()

        self._price = self._price * (1 + 0.01 * tax_rate)

    def check_availability(self, amount=1) -> bool:
        """Check if the furniture is available in stock."""
        key_f = get_index_furniture_by_values(self)
        ans: bool = False
        session = None
        try:
            if key_f is None:
                raise ValueError
            session = SessionLocal()
            row = (
                session.query(InventoryDB.quantity)
                .filter(InventoryDB.id == key_f)
                .first()
            )
            if row:
                ans = row[0] >= amount
        except ValueError:
            ValueError("There is no furniture key number.")
        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")

        finally:
            if session is not None:
                session.close()

            return ans

    def get_price(self) -> float:
        """get the furniture price."""
        if self._price is None:
            raise ValueError("Price is not set yet.")

        return self._price

    def set_price(self, price: float) -> None:
        if price is None:
            raise ValueError("Price cannot be None.")
        if not isinstance(price, (int, float)):
            raise TypeError("price must be a number.")
        if price < 0:
            raise ValueError("price must be a positive number.")
        self._price = price

    def _get_info_furniture_by_key(self) -> Tuple[int, str, str]:
        """
        Finds information about the furniture item from the database.

        Returns:
            Tuple[int, str, str]: A tuple containing the price (int), name (str),
            and description (str) of the furniture item.

        Raises:
            ValueError: If the furniture key is not found in the database.
        """
        # Initialize the variables with default values
        t_key: Optional[int] = get_index_furniture_by_values(self)
        price: int = -1
        name: str = "None"
        desc: str = "None"
        session = None

        try:
            if t_key is None:
                raise ValueError("There is no furniture key number.")

            # Open a session to query the database
            session = SessionLocal()
            result = (
                session.query(InventoryDB.price, InventoryDB.f_name, InventoryDB.f_desc)
                .filter(InventoryDB.id == t_key)
                .first()
            )

            if result:
                price, name, desc = result

        except Exception as ex:
            print(f"DB connection error: {ex}")

        finally:
            if session is not None:
                session.close()

            return price, name, desc

    @abstractmethod
    def __repr__(self) -> str:
        """Create a customized print for furniture."""
        pass

    @abstractmethod
    def _get_match_furniture(self) -> int:
        """Finding a matching furniture number"""
        pass

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class Table(Furniture, ABC):
    """
    A class representing a table, inheriting from Furniture.

    Attributes:
        color (str): The color of the table.
        material (str): The material of the table.
    """

    def __init__(self, color: str, material: str) -> None:
        """
        Initializes a Table object with a specific color and material.

        Raises:
            ValueError: If the material is invalid.
        """
        super().__init__(color)
        self._validate_material(material)  # Validating the material
        self.material: str = material

    def _validate_material(self, material: str):
        """
        Validates that the provided material is a valid option.

        Args:
            material (str): The material to be validated.

        Raises:
            TypeError: If the material is not a string.
            ValueError: If the material is not allowed based on the available materials.
        """
        # Ensure the material is a string
        if not isinstance(material, str):
            raise TypeError("Material must be a string.")

        if (
            hasattr(self.__class__, "available_materials")
            and self.__class__.available_materials is not None
        ):
            allowed = [m.lower() for m in self.__class__.available_materials]
            if material.lower() not in allowed:
                raise ValueError(
                    f"Material '{material}' is not allowed. Allowed materials: "
                    f"{', '.join(self.__class__.available_materials)}"
                )

    def __repr__(self) -> str:
        """
        Returns a string representation of the Table object, including its details.

        Returns:
            str: A formatted string with the table's name, description, price, dimensions,
            material, color, and available color options.
        """
        return (
            f"Table Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.desc}\n"
            f"  Price: ${self._price:.2f}\n"
            f"  Dimensions (L x W x H): "
            f"{self.__class__.dimensions[0]} x {self.__class__.dimensions[1]} x "
            f"{self.__class__.dimensions[2]} cm\n"
            f"  Material: {self.material}\n"
            f"  Color: {self.color}\n"
            f"  Here are several potential color options for this table:: "
            f"{', '.join(self.available_colors)}\n"
        )

    def _get_match_furniture(self, Furniture_options: list) -> str:
        """
        Searches within the range of chair IDs (chairs_key[0] to chairs_key[1])
        for an available chair in stock, and create a matching advertisement if found.

        param Furniture_options: A list of possible furniture IDs
        return: advertising -  The advertising text of the appropriate chair
        """
        chairs_key = (13, 28)
        f_desc_match: str = "None"
        is_adjustable_match: bool = False
        has_armrest_match: bool = False
        ans: bool = False
        advertising: str = "You have chosen a unique item! Good choice!"

        try:
            with SessionLocal() as session:
                for k in Furniture_options:
                    if chairs_key[0] <= k <= chairs_key[1]:
                        row = (
                            session.query(
                                InventoryDB.quantity,
                                InventoryDB.f_desc,
                                InventoryDB.is_adjustable,
                                InventoryDB.has_armrest,
                            )
                            .filter(InventoryDB.id == k)
                            .first()
                        )

                        if row:
                            if row[0] >= 1:
                                ans = True
                                f_desc_match = row[1]
                                is_adjustable_match = row[2]
                                has_armrest_match = row[3]
                                break
            if ans:
                advertising = (
                    "*** SPECIAL OFFER !!! ***    "
                    "We found a matching chair for your table! "
                    f"Description: {f_desc_match } "
                    f"Adjustable: {'Yes' if is_adjustable_match else 'No'} "
                    f"Has Armrest: {'Yes' if has_armrest_match else 'No'} "
                    "It's the perfect chair for you, and it's in stock!"
                )
        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")
        finally:
            return advertising

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class Chair(Furniture, ABC):
    """
    A class representing a chair, inheriting from Furniture.

    Attributes:
        color (str): The color of the chair.
        is_adjustable (bool): Whether the chair is adjustable.
        has_armrest (bool): Whether the chair has armrests.
    """

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool) -> None:
        """
        Initialize a Chair object with color, adjustability, and armrest properties.

        Raises:
            TypeError: If is_adjustable or has_armrest is not of type bool.
        """
        super().__init__(color)

        # Validate the types of the properties
        if not isinstance(is_adjustable, bool) or not isinstance(has_armrest, bool):
            raise TypeError("is adjustable and has armrest must be a bool.")

        self.is_adjustable: bool = is_adjustable
        self.has_armrest: bool = has_armrest

    def __repr__(self) -> str:
        """
        Returns a string representation of the Chair object, including its details.

        Returns:
            str: A formatted string with the chair's name, description, adjustability,
            armrest presence, price, dimensions, and color.
        """
        return (
            f"Chair Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.desc}\n"
            f"  Is Adjustable: {'Yes' if self.is_adjustable else 'No'}\n"
            f"  Has Armrest: {'Yes' if self.has_armrest else 'No'}\n"
            f"  Price: ${self._price:.2f}\n"
            f"  Dimensions: {self.__class__.dimensions[0]} x "
            f"{self.__class__.dimensions[1]} x {self.__class__.dimensions[2]} cm\n"
            f"  Color: {self.color}\n"
        )

    def _get_match_furniture(self, Furniture_options: list) -> str:
        """
        Searches within the range of tables IDs
        for an available table in stock, and create a matching advertisement if found.

        param Furniture_options: A list of possible furniture IDs
        return: advertising -  The advertising text of the appropriate table
        """
        tables_key: Tuple[int, int] = (1, 12)
        f_desc_match: str = "None"
        material_match: str = "None"
        ans: bool = False
        advertising: str = "You have chosen a unique item! Good choice!"

        try:
            with SessionLocal() as session:
                for k in Furniture_options:
                    if tables_key[0] <= k <= tables_key[1]:
                        row = (
                            session.query(
                                InventoryDB.quantity,
                                InventoryDB.f_desc,
                                InventoryDB.material,
                            )
                            .filter(InventoryDB.id == k)
                            .first()
                        )

                        if row:
                            if row[0] >= 1:
                                ans = True
                                f_desc_match = row[1]
                                material_match = row[2]
                                break
            if ans:
                advertising = (
                    "*** SPECIAL OFFER !!! ***    "
                    "We found a matching table for your chair! "
                    f"Description: {f_desc_match} "
                    f"Material: {material_match} "
                    "It's the perfect table for you, and it's in stock!"
                )

        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")
        finally:
            return advertising

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class DiningTable(Table):

    dimensions: Tuple[int, int, int] = (100, 50, 60)
    available_colors: List[str] = ["Brown", "Gray"]
    available_materials: List[str] = ["Wood", "Metal"]
    available_materials = ["Wood", "Metal"]
    __optimal_matches: dict[str, List[int]] = {
        "brown & wood": [13, 14],
        "brown & metal": [15, 16],
        "gray & wood": [17, 19],
        "gray & metal": [18, 20],
    }

    def __init__(self, color: str, material: str) -> None:
        """
        Initialize the DiningTable with color and material.

        Args:
            color (str): The color of the dining table.
            material (str): The material of the dining table.
        """
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the dining table based on the color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from _get_match_furniture.
        """
        key: str = f"{self.color.lower()} & {self.material.lower()}"
        matches: List[int] = DiningTable.__optimal_matches.get(key, [])

        if len(matches) == 0:
            ans = "Sorry, we did not find an item that could match your selection on our site."
        else:
            ans = self._get_match_furniture(matches)

        return ans


class WorkDesk(Table):

    dimensions: Tuple[int, int, int] = (120, 55, 65)
    available_colors: List[str] = ["Black", "White"]
    available_materials: List[str] = ["Wood", "Glass"]
    __optimal_matches: dict[str, List[int]] = {
        "black & wood": [21, 17, 24],
        "black & glass": [22, 23, 18],
        "white & wood": [25, 26, 19],
        "white & glass": [27, 28, 18],
    }

    def __init__(self, color: str, material: str) -> None:
        """
        Initialize the WorkDesk with color and material.

        Args:
            color (str): The color of the work desk.
            material (str): The material of the work desk.
        """
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the work desk based on color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from _get_match_furniture.
        """
        key: str = f"{self.color.lower()} & {self.material.lower()}"
        matches: List[int] = WorkDesk.__optimal_matches.get(key, [])

        if len(matches) == 0:
            ans = "Sorry, we did not find an item that could match your selection on our site."
        else:
            ans = self._get_match_furniture(matches)

        return ans


class CoffeeTable(Table):

    dimensions: tuple[int, int, int] = (130, 60, 70)
    available_colors: List[str] = ["Gray", "Red"]
    available_materials: List[str] = ["Glass", "Plastic"]
    __optimal_matches: dict[str, List[int]] = {
        "gray & glass": [13, 15],
        "gray & plastic": [14, 16],
        "red & glass": [17, 19],
        "red & plastic": [18, 20],
    }

    def __init__(self, color: str, material: str) -> None:
        """
        Initialize the CoffeeTable with color and material.

        Args:
            color (str): The color of the coffee table.
            material (str): The material of the coffee table.
        """
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the work desk based on color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from _get_match_furniture.
        """
        key: str = f"{self.color.lower()} & {self.material.lower()}"
        matches: List[int] = CoffeeTable.__optimal_matches.get(key, [])

        if len(matches) == 0:
            ans = "Sorry, we did not find an item that could match your selection on our site."
        else:
            ans = self._get_match_furniture(matches)

        return ans


class GamingChair(Chair):

    dimensions: tuple[int, int, int] = (150, 70, 80)
    available_colors: List[str] = ["Black", "Blue"]
    __optimal_matches: dict[str, List[int]] = {
        "black & True & True": [7, 8],
        "black & True & False": [8, 7],
        "black & False & True": [6, 8],
        "black & False & False": [8, 6],
        "blue & True & True": [5, 6],
        "blue & True & False": [6, 5],
        "blue & False & True": [5, 7],
        "blue & False & False": [7, 5],
    }

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool) -> None:
        """
        Initialize the GamingChair with color, adjustability, and armrest properties.

        Args:
            color (str): The color of the gaming chair.
            is_adjustable (bool): Whether the chair is adjustable.
            has_armrest (bool): Whether the chair has armrests.
        """
        super().__init__(color, is_adjustable, has_armrest)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching table for the gaming chair based on color, adjustability, and armrests.
        If no suitable table is found, print a message that it's a unique item.
        Otherwise, print the result from _get_match_furniture.

        This method prints an advertisement based on the available tables
        that match the color, adjustability, and armrest of the gaming chair.
        """
        key: str = f"{self.color.lower()} & {self.is_adjustable} & {self.has_armrest}"
        matches: List[int] = GamingChair.__optimal_matches.get(key, [])

        if len(matches) == 0:
            ans = "Sorry, we did not find an item that could match your selection on our site."
        else:
            ans = self._get_match_furniture(matches)

        return ans


class WorkChair(Chair):

    dimensions: tuple[int, int, int] = (140, 65, 75)
    available_colors: List[str] = ["Red", "White"]
    __optimal_matches: dict[str, List[int]] = {
        "red & True & True": [5, 7],
        "red & True & False": [5, 6],
        "red & False & True": [7, 5],
        "red & False & False": [6, 5],
        "white & True & True": [7, 8],
        "white & True & False": [6, 8],
        "white & False & True": [8, 7],
        "white & False & False": [8, 6],
    }

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool) -> None:
        """
        Initialize the WorkChair with color, adjustability, and armrest properties.

        Args:
            color (str): The color of the work chair.
            is_adjustable (bool): Whether the chair is adjustable.
            has_armrest (bool): Whether the chair has armrests.
        """
        super().__init__(color, is_adjustable, has_armrest)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching table for the work chair based on color, is_adjustable, has_armrest.
        If no suitable table is found, print a message that it's a unique item.
        Otherwise, print the result from _get_match_furniture.
        """
        key: str = f"{self.color.lower()} & {self.is_adjustable} & {self.has_armrest}"
        matches: List[int] = WorkChair.__optimal_matches.get(key, [])

        if len(matches) == 0:
            ans = "Sorry, we did not find an item that could match your selection on our site."
        else:
            ans = self._get_match_furniture(matches)

        return ans
