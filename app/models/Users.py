import bcrypt
import re
from abc import ABC, abstractmethod
from typing import Union, Optional, List, Dict
from typeguard import typechecked

from app.data.DbConnection import SessionLocal, BasicUserDB, UserDB, ManagerDB, OrdersDB
from app.models.ShoppingCart import ShoppingCart
from app.models.EnumsClass import OrderStatus
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.FurnituresClass import Chair, Table


class Authentication:
    """
    Singleton class for handling user authentication operations.

    This class provides methods for user authentication, registration,
    password hashing and validation.
    """

    _instance = None

    def __new__(cls) -> "Authentication":
        """
        Create or return the singleton instance of Authentication.

        Returns:
            Authentication: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt with salt.

        Args:
            password (str): The plain text password to hash

        Returns:
            str: The hashed password as a UTF-8 string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def validate_auth(self, password: str, hashed_password: str) -> bool:
        """
        Validate a password against its hashed version..

        Args:
            password (str): The plain text password to check
            hashed_password (str): The hashed password to compare against

        Returns:
            bool: True if the password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @typechecked
    def create_user(
        self, name: str, email: str, password: str, address: str, credit: float = 0
    ) -> Optional["User"]:
        """
        Create a new user in the database and returns User instance.

        Args:
            name (str): User's name
            email (str): User's email address
            password (str): User's plain text password (will be hashed)
            address (str): User's delivery address
            credit (float, optional): User's initial credit. Defaults to 0.

        Returns:
            Optional[User]: A new User object if successful, None if error occurs

        Raises:
            ValueError: If any input values fail validation
            TypeError: If any input types don't match expected types
        """
        # Custom validation for value constraints
        if not name.strip():
            raise ValueError("Name cannot be empty")
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
        if len(email) > 25:
            raise ValueError("Email too long")
        if not password.strip():
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if not address.strip():
            raise ValueError("Address cannot be empty")
        if not isinstance(address, str):
            raise TypeError("Address must be a string")
        if credit < 0:
            raise ValueError("Credit cannot be negative")

        session = SessionLocal()
        try:
            existing_basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if existing_basic_user:
                print("This email already exists in BasicUserDB")
                return None

            hashed_password = self._hash_password(password)

            basic_user_db = BasicUserDB(
                Uname=name, email=email, Upassword=hashed_password
            )

            user_db = UserDB(email=email, address=address, credit=credit)

            session.add(basic_user_db)
            session.add(user_db)
            session.commit()

            return User(name, email, hashed_password, address, credit)

        except Exception as e:
            session.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            session.close()

    @typechecked
    def create_manager(
        self, name: str, email: str, password: str
    ) -> Optional["Manager"]:
        """
        Create a new manager in the database.

        Args:
            name (str): Manager's name
            email (str): Manager's email address
            password (str): Manager's plain text password (will be hashed)

        Returns:
            Optional['Manager']: A new Manager object if successful, None if error occurs

        Raises:
            ValueError: If any input values fail validation
            TypeError: If any input types don't match expected types
        """
        # Custom validation for value constraints
        if not name.strip():
            raise ValueError("Name cannot be empty")
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
        if len(email) > 25:
            raise ValueError("Email too long")
        if not password.strip():
            raise ValueError("Password cannot be empty")
        if not isinstance(password, str):
            raise TypeError("Password must be a string")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        session = SessionLocal()
        try:
            existing_basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if existing_basic_user:
                print("This email already exists in BasicUserDB")
                return None

            hashed_password = self._hash_password(password)

            basic_manager_db = BasicUserDB(
                Uname=name, email=email, Upassword=hashed_password
            )

            manager_db = ManagerDB(email=email)

            session.add(basic_manager_db)
            session.add(manager_db)
            session.commit()

            return Manager(name, email, hashed_password)

        except Exception as e:
            session.rollback()
            print(f"Error creating manager: {e}")
            return None
        finally:
            session.close()

    @typechecked
    def sign_in(self, email: str, password: str) -> Optional[Union["User", "Manager"]]:
        """
        Authenticate a user or manager by email and password.

        Args:
            email (str): The email address of the user/manager
            password (str): The plain text password

        Returns:
            Optional[Union[User, Manager]]: A User or Manager object if authentication
                                           is successful, None otherwise

        Raises:
            ValueError: If any input values fail validation
            TypeError: If any input types don't match expected types
        """
        # Custom validation for value constraints
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not password.strip():
            raise ValueError("Password cannot be empty")

        session = SessionLocal()
        try:
            basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )

            if not basic_user:
                print("User does not exist")
                return None

            user = session.query(UserDB).filter(UserDB.email == email).first()
            if user and self.validate_auth(password, basic_user.Upassword):
                return User(
                    basic_user.Uname,
                    user.email,
                    basic_user.Upassword,
                    user.address,
                    user.credit,
                )

            manager = session.query(ManagerDB).filter(ManagerDB.email == email).first()
            if manager and self.validate_auth(password, basic_user.Upassword):
                return Manager(basic_user.Uname, manager.email, basic_user.Upassword)

            print("Invalid credentials or user/manager does not exist")
            return None

        except Exception as e:
            session.rollback()
            print(f"Error during login: {e}")
            return None

        finally:
            session.close()

    def set_new_password(
        self, curr_basic_user: Union["User", "Manager"], new_password: str
    ) -> None:
        """
        Update user's/manager's password in the database.

        Args:
            curr_basic_user (Union[User, Manager]): The user/manager to update
            new_password (str): The new plain text password (will be hashed)

        Raises:
            ValueError: If user/manager not found in database
            Exception: If an error occurs during password update
        """
        if not isinstance(new_password, str):
            raise TypeError("password must be a string")
        if len(new_password) < 8:
            raise ValueError("new_password lenght not valid")

        session = SessionLocal()
        try:
            basic_user_db = (
                session.query(BasicUserDB)
                .filter(BasicUserDB.email == curr_basic_user.email)
                .first()
            )
            if not basic_user_db:
                raise ValueError

            hashed_password = self._hash_password(new_password)
            basic_user_db.Upassword = hashed_password

            session.commit()
            print(f"Password successfully changed for:\n{curr_basic_user}")

        except ValueError:
            session.rollback()
            raise ValueError("User/Manager not found in database")

        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating password: {e}")
        finally:
            session.close()

    @staticmethod
    def validate_credit_card(total_price: int, credit_card_num: int) -> bool:
        """
        Mock Validation of a credit card for payment.

        Args:
            total_price (int): The total price of the purchase
            credit_card_num (int): The credit card number

        Returns:
            bool: True if the credit card is valid, False otherwise
        """
        if not total_price:
            return True
        if isinstance(credit_card_num, int):
            return True
        return False


class BasicUser(ABC):
    """
    Abstract base class for all user types in the system..

    This class provides common functionality for user authentication and validation.

    Attributes:
        name (str): User's name
        email (str): User's validated email address
        password (str): User's hashed password
    """

    def __init__(self, name: str, email: str, password: str) -> None:
        """
        Initialize a new User instance.

        Note: This should only be called by the Authentication class.

        Args:
            name (str): User's name
            email (str): User's email address (will be validated)
            password (str): User's hashed password

        Raises:
            ValueError: If the email format is invalid
        """
        if not name.strip():
            raise ValueError("Name cannot be empty")
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
        if len(email) > 25:
            raise ValueError("Email too long")
        if not password.strip():
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("password length not valid")
        if not isinstance(password, str):
            raise TypeError("Password must be a string")

        self.name = name
        self.email = self.__validate_email(email)
        self.__password = password  # Already hashed by Authentication

    @property
    def password(self):
        return self.__password

    def __validate_email(self, email: str) -> str:
        """
        Validate email format using regex.

        Args:
            email (str): Email address to validate

        Returns:
            str: Validated email address (lowercase)

        Raises:
            ValueError: If email format is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()

    @abstractmethod
    def set_password(self, new_password: str) -> None:
        """
        Set a new password for the user.

        Args:
            new_password (str): The new plain text password
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """
        Return a string representation of the user.

        Returns:
            str: A string representation of the user
        """
        pass


class User(BasicUser):
    """
    User class for managing user authentication and profile information in the furniture store.

    Attributes:
        name (str): User's name
        email (str): User's email address
        password (str): Hashed password
        address (str): User's delivery address
        credit (float): User's credit available to spend
        cart (ShoppingCart): User's shopping cart
        orders (List[Order]): List of user's orders
    """

    def __init__(
        self, name: str, email: str, password: str, address: str, credit: float = 0
    ) -> None:
        """
        Initialize a new User instance.

        Note: This should only be called by the Authentication class.

        Args:
            name (str): User's name
            email (str): User's email address
            password (str): User's hashed password
            address (str): User's delivery address
            credit (float, optional): User's initial credit. Defaults to 0.
        """
        super().__init__(name, email, password)
        if not isinstance(address, str):
            raise TypeError("Address must be a string")
        if len(address) > 255 or len(address) < 1:
            raise ValueError("Address length not valid.")
        self.address = address
        self.__credit = credit
        self.cart = ShoppingCart()
        self._orders: List[Order] = []

    @property
    def credit(self):
        return self.__credit

    def update_user_details(
        self, address: Optional[str] = None, name: Optional[str] = None
    ) -> None:
        """
        Update user profile information.

        Args:
            address (Optional[str], optional): New address. Defaults to None.
            name (Optional[str], optional): New name. Defaults to None.

        Raises:
            ValueError: If user not found in database
            Exception: If an error occurs during update
        """
        if address is None and name is None:
            return

        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError

            basic_user_db = (
                session.query(BasicUserDB)
                .filter(BasicUserDB.email == self.email)
                .first()
            )

            if address is not None:
                user_db.address = address
                self.address = address
            if name is not None:
                basic_user_db.Uname = name
                self.name = name

            session.commit()
        except ValueError:
            session.rollback()
            raise ValueError("User not found in database")
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating user details: {e}")
        finally:
            session.close()

    def update_credit(self, credit: float) -> None:
        """
        Update user's credit balance.

        Args:
            credit (float): Amount to add to user's credit (can be negative)

        Raises:
            ValueError: If user not found in database
            Exception: If an error occurs during update
        """

        if not isinstance(credit, (int, float)):
            raise TypeError("credit must be a number")
        try:
            session = SessionLocal()
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError

            user_db.credit += credit
            self.__credit = user_db.credit
            session.commit()
        except ValueError:
            session.rollback()
            raise ValueError("User not found in database")
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating credit: {e}")
        finally:
            session.close()

    def view_cart(self) -> str:
        """
        Get a string representation of the user's shopping cart.

        Returns:
            str: String representation of the cart
        """
        cart_data = {}
        if len(self.cart.items) > 0:
            for item in self.cart:
                cart_data[item[0].name] = item[1]
        return cart_data

    def get_order_hist(self) -> List[Order]:
        """
        Retrieve user's order history.

        Returns:
            List[Order]: List of Order objects associated with the user
        """
        return self._orders

    def set_password(self, new_password: str) -> None:
        """
        Set a new password for the user.

        Args:
            new_password (str): The new plain text password
        """
        Authentication().set_new_password(self, new_password)
        return

    def checkout(self, credit_card_num: int, coupon_code: Optional[str] = None) -> bool:
        """
        Process checkout of items in the shopping cart.

        Args:
            credit_card_num (int): Credit card number for payment
            coupon_code (Optional[str], optional): Discount coupon code. Defaults to None.

        Returns:
            bool: True if checkout was successful, False otherwise

        Raises:
            ValueError: If cart is empty, item quantity is invalid, or credit card is invalid
        """
        try:
            ans = False
            if self.cart.items:
                for item, quantity in self.cart.items:
                    if not item.check_availability(quantity):
                        raise ValueError(f"There is not enough:{item} in the inventory")
            else:
                raise ValueError("There are no items in the cart")

            if coupon_code:
                discount_percent, coupon_id = self.cart.get_coupon_discount_and_id(
                    coupon_code
                )
                total_price = self.cart.apply_discount(discount_percent)
            else:
                total_price = self.cart.get_total_price()
                coupon_id = None

            if self.__credit:
                if self.__credit <= total_price:
                    total_price -= self.__credit
                    self.update_credit(self.__credit * -1)
                else:
                    self.update_credit(total_price * -1)
                    total_price = 0

            if Authentication.validate_credit_card(total_price, credit_card_num):
                inv = Inventory()
                for item, amount in self.cart.items:
                    if amount < 0 or not isinstance(amount, int):
                        raise ValueError(f"item {item} has invalid quantity")
                    inv.update_amount_in_inventory(item, amount, sign=False)
            else:
                raise ValueError("Invalid Credit Card")

            new_order = Order(self.email, self.cart, coupon_id)
            self._orders.append(new_order)
            ans = True

        except Exception as e:
            print(f"Error in checkout Proc: {e}")
        finally:
            return ans

    def __repr__(self) -> str:
        """
        String representation of the User object.

        Returns:
            str: String representation of the user
        """
        return (
            f"User: Name ={self.name}, Email={self.email},"
            f"Address={self.address}, Credit={self.credit}"
        )


class Manager(BasicUser):
    """
    Manager class for administrative operations in the furniture store.

    Managers can manage users, inventory, and orders in the system.

    Attributes:
        name (str): Manager's name
        email (str): Manager's email address
        password (str): Manager's hashed password
    """

    def __init__(self, name: str, email: str, password: str) -> None:
        """
        Initialize a new Manager instance.

        Note: This should only be called by the Authentication class.

        Args:
            name (str): Manager's name
            email (str): Manager's email address
            password (str): Manager's hashed password
        """
        super().__init__(name, email, password)
        if not name.strip():
            raise ValueError("Name cannot be empty")
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not email.strip():
            raise ValueError("Email cannot be empty")
        if not isinstance(email, str):
            raise TypeError("Email must be a string")
        if len(email) > 25:
            raise ValueError("Email too long")
        if not password.strip():
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not isinstance(password, str):
            raise TypeError("Password must be a string")

    def __repr__(self) -> str:
        """
        String representation of the Manager object.

        Returns:
            str: String representation of the manager
        """
        return f"Manager: Name = {self.name}, Email = {self.email}"

    def to_dict_without_password(self) -> Dict:
        """convert manager to dict"""
        return {"name": self.name, "email": self.email}

    def delete_user(self, email: str) -> None:
        """
        Delete user from databases.

        Args:
            email (str): Email of the user to delete

        Raises:
            Exception: If an error occurs during deletion
        """
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == email).first()
            basic_user_db = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if user_db:
                session.delete(user_db)
            if basic_user_db:
                session.delete(basic_user_db)

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error deleting user: {e}")
        finally:
            session.close()

    def set_password(self, new_password: str) -> None:
        """
        Set a new password for the manager.

        Args:
            new_password (str): The new plain text password
        """
        Authentication().set_new_password(self, new_password)
        return

    def add_manager(self, name: str, email: str, password: str) -> Optional["Manager"]:
        """
        Add a new manager to the system.

        Args:
            name (str): New manager's name
            email (str): New manager's email
            password (str): New manager's plain text password

        Returns:
            Optional['Manager']: New Manager object if successful, None otherwise
        """
        return Authentication().create_manager(name, email, password)

    def update_order_status(self, order_id: int) -> None:
        """
        Update order status in Database.

        Args:
            order_id (int): ID of the order to update

        Raises:
            ValueError: If order is already delivered
            Exception: If an error occurs during update
        """
        session = SessionLocal()
        try:
            order_db = session.query(OrdersDB).filter(OrdersDB.id == order_id).first()
            if order_db.id == OrderStatus.DELIVERED:
                raise ValueError
            else:
                order_db.Ostatus += 1
            session.commit()
        except ValueError:
            session.rollback()
            raise ValueError(f"Order number {order_id} already delivered")
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating Order status: {e}")
        finally:
            session.close()

    def update_inventory(
        self, item: Union[Chair, Table], quantity: int, sign: int
    ) -> None:
        """
        Update inventory item quantity.

        Args:
            item (Union[Chair, Table]): Furniture item to update
            quantity (int): Quantity to add or remove
            f_type_enum (int): Furniture type enum value
            sign (int): 1 for addition, 0 for subtraction

        Raises:
            ValueError: If quantity is negative or sign is invalid
            Exception: If an error occurs during update
        """
        inv = Inventory()
        try:
            if quantity < 0:
                raise ValueError("Quantity must be non-negative")
            if sign not in [0, 1]:
                raise ValueError("Sign must be 1 or 0.")

        except Exception as e:
            raise Exception(f"Error updating Inventory: {e}")
        inv.update_amount_in_inventory(item, quantity, sign)
        return

    def get_all_orders(self) -> None:
        """
        Retrieve and display all orders from the database.

        Prints all orders in a structured format.

        Raises:
            Exception: If an error occurs during retrieval
        """
        session = SessionLocal()
        try:
            orders = session.query(OrdersDB).all()

            for order in orders:
                print("=" * 50)
                print(f"Order ID        : {order.id}")
                print(f"Status          : {order.Ostatus}")
                print(f"User Email      : {order.UserEmail}")
                print(
                    f"Coupon Code ID  : {order.idCouponsCodes if order.idCouponsCodes else 'None'}"
                )
                print("=" * 50)
                print()

        except Exception as e:
            session.rollback()
            raise Exception(f"Error retrieving orders: {e}")
        finally:
            session.close()
