from sqlalchemy import and_
from abc import ABC, abstractmethod
from app.models.EnumsClass import FurnitureType
from app.data.DbConnection import SessionLocal, InventoryDB
from app.utils import transform_pascal_to_snake

class Furniture(ABC):
    def __init__(self, color: str):
        self._validate_color(color)  # Checking that the color matches
        self.color = color
        self.price = None
        
    def _validate_color(self, color):
        """ Checking that the color matches the color options """
        if not isinstance(color, str):
            raise TypeError("Color must be a string.")
        if hasattr(self.__class__, 'available_colors') and self.__class__.available_colors is not None:
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
        """ Return the color of the furniture. """
        return self.color

    @abstractmethod
    def check_availability(self) -> bool:
        """ Check if the furniture is available in stock. """
        pass


    def get_price(self) -> float:
        """ get the furniture price. """
        if self.price is None:
            raise ValueError("Price is not set yet.")
        return self.price

    @abstractmethod
    def __repr__(self) -> str:
        """ Create a customized print for furniture. """
        pass

    @abstractmethod
    def _get_info_furniture_by_values(self, *args):
        """ Finding information about the item from the BD """
        pass


class Table(Furniture):
    
    def __init__(self, color: str, material: str):
        super().__init__(color)
        self._validate_material(material)
        self.material = material
        price, name, desc = self._get_info_furniture_by_values(color, material, self.__class__.__name__)
        self.price = price
        self.name = name
        self.desc = desc 

    
    def _get_info_furniture_by_values(self, color, material, f_type):
        """ Finding information about the item from the BD """
        furniture_type = transform_pascal_to_snake(f_type)
        furniture_type = FurnitureType[furniture_type].value
        price = -1
        name = "None"
        desc = "None"
        try:
            with SessionLocal() as session:
                try:
                    result = session.query(InventoryDB.price, InventoryDB.f_name, InventoryDB.f_desc).filter(
                            and_(
                                InventoryDB.furniture_type == furniture_type,
                                InventoryDB.color == color,
                                InventoryDB.material == material
                            )
                        ).first()
                    if result:
                        price = result[0]
                        name = result[1]
                        desc = result[2]
                except Exception as e:
                    print(f"Error fetching data: {e}")
        except Exception as ex:
            print(f"DB connection error: {ex}")
        finally:
            session.close()
            return price, name, desc 
    
    def _validate_material(self, material: str):
        """ Checking that the material matches the material options """
        if not isinstance(material, str):
            raise TypeError("Material must be a string.")
        if hasattr(self.__class__, 'available_materials') and self.__class__.available_materials is not None:
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


    def check_availability(self, amount = 1) -> bool:
        """ Check if table is in stock. """
        curr_quantity = None
        ans = False
        furniture_type = transform_pascal_to_snake(self.__class__.__name__)
        furniture_type = FurnitureType[furniture_type].value
        try:
            with SessionLocal() as session:
                try:
                    curr_quantity = session.query(InventoryDB.quantity).filter(
                            and_(
                                InventoryDB.furniture_type == furniture_type,
                                InventoryDB.color == self.color,
                                InventoryDB.material == self.material
                            )
                        ).first()
                    if curr_quantity:
                        ans = curr_quantity[0] >= amount                     
                except Exception as e:
                    print(f"Error fetching data: {e}")
        except Exception as ex:
            print(f"DB connection error: {ex}")
        finally:
            session.close()
            return ans 

    @abstractmethod
    def get_matching_chair(self) -> "Chair":
        """Abstract method to get a matching chair for the table."""
        pass


class Chair(Furniture):
    
    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color)
        if not isinstance(is_adjustable, bool) or not isinstance(has_armrest, bool):
            raise TypeError("is adjustable and has armrest must be a bool.")
        self.is_adjustable = is_adjustable  
        self.has_armrest = has_armrest
        price, name, desc = self._get_info_furniture_by_values(color, is_adjustable, has_armrest, self.__class__.__name__)
        self.price = price
        self.name = name
        self.desc = desc    
    
    def _get_info_furniture_by_values(self, color, is_adjustable, has_armrest, f_type):
        """ Finding information about the item from the BD """
        furniture_type = transform_pascal_to_snake(f_type)
        furniture_type = FurnitureType[furniture_type].value
        price = -1
        name = "None"
        desc = "None"
        session = None 
        try:
            session = SessionLocal()
            result = session.query(
                InventoryDB.price,
                InventoryDB.f_name,
                InventoryDB.f_desc
            ).filter(
                and_(
                    InventoryDB.furniture_type == furniture_type,
                    InventoryDB.color == color,
                    InventoryDB.is_adjustable == is_adjustable,
                    InventoryDB.has_armrest == has_armrest,
                )
            ).first()
            if result:
                price, name, desc = result  # Unpack the tuple
        except Exception as ex:
            print(f"DB connection or query error: {ex}")
        finally:
            if session is not None:
                session.close()
            return price, name, desc
    
    
    def check_availability(self, amount = 1) -> bool:
        """ Check if chair is in stock. """
        curr_quantity = None
        ans = False
        furniture_type = transform_pascal_to_snake(self.__class__.__name__)
        furniture_type = FurnitureType[furniture_type].value
        try:
            with SessionLocal() as session:
                try:
                    curr_quantity = session.query(InventoryDB.quantity).filter(
                            and_(
                                InventoryDB.furniture_type == furniture_type,
                                InventoryDB.color == self.color,
                                InventoryDB.is_adjustable == self.is_adjustable,
                                InventoryDB.has_armrest == self.has_armrest,
                            )
                        ).first()
                    if curr_quantity:
                        ans = curr_quantity[0] >= amount                     
                except Exception as e:
                    print(f"Error fetching data: {e}")
        except Exception as ex:
            print(f"DB connection error: {ex}")
        finally:
            session.close()
            return ans 
    

    
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


    @abstractmethod
    def get_matching_table(self) -> Table:
        """Abstract method to get a matching chair for the table."""
        pass


class DiningTable(Table):
    
    dimensions = (100, 50, 60)
    available_colors = ["Brown", "Gray"]
    available_materials = ["Wood","Metal"]
            
    def __init__(self, color: str, material: str):
        super().__init__( color, material)


    def get_matching_chair(self) -> str:
        """Find a matching chair for the dining table. """
        pass  # To be implemented later based on matching criteria.


class WorkDesk(Table):
    
    dimensions = (120, 55, 65)
    available_colors = ["Black", "White"]
    available_materials = ["Wood","Glass"]
    
    def __init__(self, color: str, material: str):
        super().__init__(color, material)


    def get_matching_chair(self) -> str:
        """Find a matching chair for the wort table. """
        pass  # To be implemented later based on matching criteria.


class CoffeeTable(Table):
    
    dimensions = (130, 60, 70)
    available_colors = ["Gray", "Red"]
    available_materials = ["Glass","Plastic"]
            
    def __init__(self, color: str, material: str):
        super().__init__(color, material)


    def get_matching_chair(self) -> str:
        """Find a matching chair for the coffee table. """
        pass  # To be implemented later based on matching criteria.


class GamingChair(Chair):
    
    dimensions = (150, 70, 80)
    available_colors = ["Black", "Blue"]
        
    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color, is_adjustable, has_armrest)


    def get_matching_table(self) -> Table:
        """
        Find a matching table for the gaming chair.
        Returns a Table object.
        """
        pass  # To be implemented later based on matching criteria.


class WorkChair(Chair):
    
    dimensions = (140, 65, 75)
    available_colors = ["Red", "White"]
        
    def __init__(self, color: str, is_adjustable: bool, has_armrest: bool):
        super().__init__(color, is_adjustable, has_armrest)


    def get_matching_table(self) -> Table:
        """
        Find a matching table for the work chair.
        Returns a Table object.
        """
        pass  # To be implemented later based on matching criteria.


