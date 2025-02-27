from enum import Enum


class FurnitureType(Enum):
    """Represents the different types of furniture."""

    DINING_TABLE = 1
    WORK_DESK = 2
    COFFEE_TABLE = 3
    WORK_CHAIR = 4
    GAMING_CHAIR = 5


class OrderStatus(Enum):
    """Represents the different statuses of an order."""

    PENDING = 1
    SHIPPED = 2
    DELIVERED = 3
