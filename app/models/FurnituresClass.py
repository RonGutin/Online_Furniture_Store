from abc import ABC, abstractmethod
from app.data.DbConnection import SessionLocal, InventoryDB
from app.models.inventory import Inventory


class Furniture(ABC):

    def __init__(self, color: str):
        self._validate_color(color)  # Checking that the color matches
        self.color = color
        price, name, desc = self._get_info_furniture_by_key()
        self.price = price
        self.name = name
        self.desc = desc

    def _validate_color(self, color: str) -> None:
        """Checking that the color matches the color options"""
        if not isinstance(color, str):
            raise TypeError("Color must be a string.")
        if (
            hasattr(self.__class__, "available_colors")
            and self.__class__.available_colors is not None
        ):
            allowed = [c.lower() for c in self.__class__.available_colors]
            if color.lower() not in allowed:
                raise ValueError(
                    f"Color '{color}' is not allowed. Allowed colors: {', '.join(self.__class__.available_colors)}"
                )

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

    def check_availability(self, amount=1) -> bool:
        """Check if the furniture is available in stock."""
        inv = Inventory()
        key_f = inv.get_index_furniture_by_values(self)
        ans = False
        session = None
        try:
            if key_f is None:
                raise ValueError("There is no furniture key number.")
            session = SessionLocal()
            row = (
                session.query(InventoryDB.quantity)
                .filter(InventoryDB.id == key_f)
                .first()
            )
            if row:
                ans = row[0] >= amount
        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")
        finally:
            if session is not None:
                session.close()
            return ans

    def get_price(self) -> float:
        """get the furniture price."""
        if self.price is None:
            raise ValueError("Price is not set yet.")
        return self.price

    def _get_info_furniture_by_key(self) -> tuple[int, str, str]:
        """Finding information about the item from the DB."""
        inv = Inventory()
        t_key = inv.get_index_furniture_by_values(self)
        price = -1
        name = "None"
        desc = "None"
        session = None
        try:
            if t_key is None:
                raise ValueError("There is no furniture key number.")
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
    def get_match_furniture(self) -> int:
        """Finding a matching furniture number"""
        pass

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class Table(Furniture):

    def __init__(self, color: str, material: str):
        super().__init__(color)
        self._validate_material(material)
        self.material = material

    def _validate_material(self, material: str):
        """Checking that the material matches the material options"""
        if not isinstance(material, str):
            raise TypeError("Material must be a string.")
        if (
            hasattr(self.__class__, "available_materials")
            and self.__class__.available_materials is not None
        ):
            allowed = [m.lower() for m in self.__class__.available_materials]
            if material.lower() not in allowed:
                raise ValueError(
                    f"Material '{material}' is not allowed. Allowed materials: {', '.join(self.__class__.available_materials)}"
                )

    def __repr__(self) -> str:
        return (
            f"Table Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.desc}\n"
            f"  Price: ${self.price:.2f}\n"
            f"  Dimensions (L x W x H): {self.__class__.dimensions[0]} x {self.__class__.dimensions[1]} x {self.__class__.dimensions[2]} cm\n"
            f"  Material: {self.material}\n"
            f"  Color: {self.color}\n"
            f"  Here are several potential color options for this table:: {', '.join(self.available_colors)}\n"
        )

    def get_match_furniture(self, Furniture_options: list) -> str:
        """
        Searches within the range of chair IDs (chairs_key[0] to chairs_key[1])
        for an available chair in stock, and create a matching advertisement if found.

        param Furniture_options: A list of possible furniture IDs
        return: advertising -  The advertising text of the appropriate chair
        """
        chairs_key = (13, 28)
        f_desc_match = "None"
        is_adjustable_match = False
        has_armrest_match = False
        ans = False
        advertising = "You have chosen a unique item! Good choice!"

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
                    "*** SPECIAL OFFER !!! ***\n"
                    "We found a matching chair for your table!\n"
                    f"Description: {f_desc_match}\n"
                    f"Adjustable: {'Yes' if is_adjustable_match else 'No'}\n"
                    f"Has Armrest: {'Yes' if has_armrest_match else 'No'}\n"
                    "It's the perfect chair for you, and it's in stock!"
                )
        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")

        return advertising

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class Chair(Furniture):

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color)
        if not isinstance(is_adjustable, bool) or not isinstance(has_armrest, bool):
            raise TypeError("is adjustable and has armrest must be a bool.")
        self.is_adjustable = is_adjustable
        self.has_armrest = has_armrest

    def __repr__(self) -> str:
        return (
            f"Chair Details:\n"
            f"  Name: {self.name}\n"
            f"  Description: {self.desc}\n"
            f"  Is Adjustable: {'Yes' if self.is_adjustable else 'No'}\n"
            f"  Has Armrest: {'Yes' if self.has_armrest else 'No'}\n"
            f"  Price: ${self.price:.2f}\n"
            f"  Dimensions: {self.__class__.dimensions[0]} x {self.__class__.dimensions[1]} x {self.__class__.dimensions[2]} cm\n"
            f"  Color: {self.color}\n"
        )

    def get_match_furniture(self, Furniture_options: list) -> str:
        """
        Searches within the range of tables IDs
        for an available table in stock, and create a matching advertisement if found.

        param Furniture_options: A list of possible furniture IDs
        return: advertising -  The advertising text of the appropriate table
        """
        tables_key = (1, 12)
        f_desc_match = "None"
        material_match = "None"
        ans = False
        advertising = "You have chosen a unique item! Good choice!"

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
                    "*** SPECIAL OFFER !!! ***\n"
                    "We found a matching table for your chair!\n"
                    f"Description: {f_desc_match}\n"
                    f"Material: {material_match}\n"
                    "It's the perfect table for you, and it's in stock!"
                )

        except Exception as ex:
            print(f"Error connecting to DB or fetching data: {ex}")

        return advertising

    @abstractmethod
    def Print_matching_product_advertisement(self) -> None:
        """Print a matching product advertisement"""
        pass


class DiningTable(Table):

    dimensions = (100, 50, 60)
    available_colors = ["Brown", "Gray"]
    available_materials = ["Wood", "Metal"]
    __optimal_matches = {
        "brown & wood": [13, 14],
        "brown & metal": [15, 16],
        "gray & wood": [17, 19],
        "gray & metal": [18, 20],
    }

    def __init__(self, color: str, material: str):
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the dining table based on the color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from get_match_furniture.
        """
        key = f"{self.color.lower()} & {self.material.lower()}"
        matches = DiningTable.__optimal_matches.get(key, [])
        ans = self.get_match_furniture(matches)
        print(ans)


class WorkDesk(Table):

    dimensions = (120, 55, 65)
    available_colors = ["Black", "White"]
    available_materials = ["Wood", "Glass"]
    __optimal_matches = {
        "black & wood": [21, 17, 24],
        "black & glass": [22, 23, 18],
        "white & wood": [25, 26, 19],
        "white & glass": [27, 28, 18],
    }

    def __init__(self, color: str, material: str):
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the work desk based on color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from get_match_furniture.
        """
        key = f"{self.color.lower()} & {self.material.lower()}"
        matches = WorkDesk.__optimal_matches.get(key, [])
        ans = self.get_match_furniture(matches)
        print(ans)


class CoffeeTable(Table):

    dimensions = (130, 60, 70)
    available_colors = ["Gray", "Red"]
    available_materials = ["Glass", "Plastic"]
    __optimal_matches = {
        "gray & glass": [13, 15],
        "gray & plastic": [14, 16],
        "red & glass": [17, 19],
        "red & plastic": [18, 20],
    }

    def __init__(self, color: str, material: str):
        super().__init__(color, material)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching chair for the work desk based on color & material.
        If no suitable chair is found, print a message that it's a unique item.
        Otherwise, print the result from get_match_furniture.
        """
        key = f"{self.color.lower()} & {self.material.lower()}"
        matches = CoffeeTable.__optimal_matches.get(key, [])
        ans = self.get_match_furniture(matches)
        print(ans)


class GamingChair(Chair):

    dimensions = (150, 70, 80)
    available_colors = ["Black", "Blue"]
    __optimal_matches = {
        "black & True & True": [7, 8],
        "black & True & False": [8, 7],
        "black & False & True": [6, 8],
        "black & False & False": [8, 6],
        "blue & True & True": [5, 6],
        "blue & True & False": [6, 5],
        "blue & False & True": [5, 7],
        "blue & False & False": [7, 5],
    }

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color, is_adjustable, has_armrest)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching table for the gaming chair based on color, is_adjustable, has_armrest.
        If no suitable table is found, print a message that it's a unique item.
        Otherwise, print the result from get_match_furniture.
        """
        key = f"{self.color.lower()} & {self.is_adjustable} & {self.has_armrest}"
        matches = GamingChair.__optimal_matches.get(key, [])
        ans = self.get_match_furniture(matches)
        print(ans)


class WorkChair(Chair):

    dimensions = (140, 65, 75)
    available_colors = ["Red", "White"]
    __optimal_matches = {
        "red & True & True": [5, 7],
        "red & True & False": [5, 6],
        "red & False & True": [7, 5],
        "red & False & False": [6, 5],
        "white & True & True": [7, 8],
        "white & True & False": [6, 8],
        "white & False & True": [8, 7],
        "white & False & False": [8, 6],
    }

    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color, is_adjustable, has_armrest)

    def Print_matching_product_advertisement(self) -> None:
        """
        Find a matching table for the work chair based on color, is_adjustable, has_armrest.
        If no suitable table is found, print a message that it's a unique item.
        Otherwise, print the result from get_match_furniture.
        """
        key = f"{self.color.lower()} & {self.is_adjustable} & {self.has_armrest}"
        matches = WorkChair.__optimal_matches.get(key, [])
        ans = self.get_match_furniture(matches)
        print(ans)
