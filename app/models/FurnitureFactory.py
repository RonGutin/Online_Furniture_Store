from typing import Optional, Union
from app.models.EnumsClass import (
    FurnitureType,
)  # Import FurnitureType from the enums module
from app.models.FurnituresClass import (
    DiningTable,
    WorkDesk,
    CoffeeTable,
    WorkChair,
    GamingChair,
)


class FurnitureFactory:
    """
    Singleton factory class responsible for creating furniture objects.
    """

    _instance: Optional["FurnitureFactory"] = None

    def __new__(cls) -> "FurnitureFactory":
        """
        Ensures that only one instance of FurnitureFactory exists.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_furniture(
        self, furniture_type: str, **kwargs
    ) -> Union[DiningTable, WorkDesk, CoffeeTable, WorkChair, GamingChair]:
        """
        Creates a furniture object based on the given furniture type.

        Args:
            furniture_type (str): The type of furniture to create.
            **kwargs: Additional arguments for the furniture object.

        Returns:
            An instance of the appropriate furniture class.

        Raises:
            ValueError: If the furniture type is unknown.
        """
        if not isinstance(furniture_type, str):
            raise TypeError("furniture_type must be an string")
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
