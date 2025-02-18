from app.models.EnumsClass import FurnitureType  # Import FurnitureType from the enums module
from app.models.FurnituresClass import DiningTable, WorkDesk, CoffeeTable, WorkChair, GamingChair


class FurnitureFactory:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_furniture(self, furniture_type: str, **kwargs):
        """
        A function that creates a piece of furniture.
        Type the desired piece of furniture in the format appropriate for an Enum
        """
        try:
            enum_type = FurnitureType[furniture_type.upper()]
        except KeyError:
            raise ValueError(f"Unknown furniture type: {furniture_type}")

        if enum_type.value == 1:  # DINING_TABLE
            return DiningTable(**kwargs)
        elif enum_type.value == 2:  # WORK_DESK
            return WorkDesk(**kwargs)
        elif enum_type.value == 3:  # COFFEE_TABLE
            return CoffeeTable(**kwargs)
        elif enum_type.value == 4:  # WORK_CHAIR
            return WorkChair(**kwargs)
        elif enum_type.value == 5:  # GAMING_CHAIR
            return GamingChair(**kwargs)
        else:
            raise ValueError(f"Unknown furniture type value: {enum_type.value}")


