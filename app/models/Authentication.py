import bcrypt
from typing import Union, Optional

from app.data.DbConnection import SessionLocal, BasicUserDB, UserDB, ManagerDB
from app.models.Users import User, Manager


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
        Validate a password against its hashed version.

        Args:
            password (str): The plain text password to check
            hashed_password (str): The hashed password to compare against

        Returns:
            bool: True if the password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_user(
        self, name: str, email: str, password: str, address: str, credit: float = 0
    ) -> Optional[User]:
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
        """
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
                name=name, email=email, password=hashed_password
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
        """
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
                name=name, email=email, password=hashed_password
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

    def sign_in(self, email: str, password: str) -> Optional[Union[User, Manager]]:
        """
        Authenticate a user or manager by email and password.

        Args:
            email (str): The email address of the user/manager
            password (str): The plain text password

        Returns:
            Optional[Union[User, Manager]]: A User or Manager object if authentication
                                           is successful, None otherwise
        """
        session = SessionLocal()
        try:
            basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            user = session.query(UserDB).filter(UserDB.email == email).first()
            if user and self.validate_auth(password, basic_user.password):
                return User(
                    basic_user.Uname,
                    user.email,
                    basic_user.Upassword,
                    user.address,
                    user.credit,
                )

            manager = session.query(ManagerDB).filter(ManagerDB.email == email).first()
            if manager and self.validateAuth(password, manager.password):
                return Manager(manager.name, manager.email, manager.password)

            print("Invalid credentials or user/manager does not exist")
            return None

        except Exception as e:
            session.rollback()
            print(f"Error during login: {e}")
            return None

        finally:
            session.close()

    def set_new_password(
        self, curr_basic_user: Union[User, Manager, None], new_password: str
    ) -> None:
        """
        Update user's/manager's password in the database.

        Args:
            curr_basic_user (Union[User, Manager, None]): The user/manager to update
            new_password (str): The new plain text password (will be hashed)

        Raises:
            ValueError: If user/manager not found in database
            Exception: If an error occurs during password update
        """
        session = SessionLocal()
        try:
            basic_user_db = (
                session.query(BasicUserDB)
                .filter(BasicUserDB.email == curr_basic_user.email)
                .first()
            )
            if not basic_user_db:
                raise ValueError("User/Manager not found in database")

            hashed_password = self._hash_password(new_password)
            basic_user_db.Upassword = hashed_password

            session.commit()
            print(f"Password successfully changed for:\n{curr_basic_user}")

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
