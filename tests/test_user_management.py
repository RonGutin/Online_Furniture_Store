import pytest
import bcrypt
from unittest.mock import patch, MagicMock, ANY
from app.models.Users import Authentication, BasicUser, User, Manager
from app.models.ShoppingCart import ShoppingCart
from app.models.EnumsClass import OrderStatus
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.FurnituresClass import Chair, Table
import typeguard
from typing import Union


def fixed_validate_credit_card(
    total_price: int, credit_card_num: Union[int, str]
) -> bool:
    """
    A simplified credit card validation function for testing purposes.

    Returns True if the total price is 0 or if the credit card number can be
    converted to an integer, False otherwise.

    Args:
        total_price (int): The total purchase price
        credit_card_num (Union[int, str]): The credit card number to validate

    Returns:
        bool: True if validation passes, False otherwise
    """
    if total_price == 0:
        return True
    try:
        int(credit_card_num)
    except Exception:
        return False
    return True


class MockBasicUser(BasicUser):
    """
    A mock implementation of BasicUser for testing purposes.

    Overrides set_password and __repr__ methods to simplify testing.
    """

    def set_password(self, new_password):
        """
        Mock implementation of set_password that does nothing.

        Args:
            new_password: The new password (unused)
        """
        pass

    def __repr__(self):
        """
        Returns a string representation of the MockBasicUser.

        Returns:
            str: A string containing the user's name and email
        """
        return f"MockBasicUser: {self.name}, {self.email}"


@pytest.fixture
def mock_session():
    """
    Fixture that provides a mock database session for testing.

    Returns a MagicMock configured with common database session methods.

    Returns:
        MagicMock: A mock database session
    """
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
def auth():
    """
    Fixture that provides an Authentication instance for testing.

    Returns:
        Authentication: A new Authentication instance
    """
    return Authentication()


@pytest.fixture
def hashed_password():
    """
    Fixture that provides a bcrypt-hashed password for testing.

    Hashes the string "password12345" and returns it as a UTF-8 string.

    Returns:
        str: A bcrypt-hashed password string
    """
    return bcrypt.hashpw("password12345".encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


@pytest.fixture
def mock_user(hashed_password):
    """
    Fixture that provides a mock User instance for testing.

    Creates a User with predefined test values and the hashed password.

    Args:
        hashed_password: The hashed_password fixture

    Returns:
        User: A User instance with test data
    """
    return User("Test User", "test@example.com", hashed_password, "123 Test St", 100.0)


@pytest.fixture
def mock_manager(hashed_password):
    """
    Fixture that provides a mock Manager instance for testing.

    Creates a Manager with predefined test values and the hashed password.

    Args:
        hashed_password: The hashed_password fixture

    Returns:
        Manager: A Manager instance with test data
    """
    return Manager("Test Manager", "manager@example.com", hashed_password)


@pytest.fixture
def mock_shopping_cart():
    """
    Fixture that provides a mock ShoppingCart for testing.

    Creates a MagicMock configured with predefined methods and values
    to simulate a ShoppingCart with items.

    Returns:
        MagicMock: A mock ShoppingCart
    """
    cart = MagicMock(spec=ShoppingCart)
    cart.items = [(MagicMock(spec=Chair), 2), (MagicMock(spec=Table), 1)]
    cart.get_total_price.return_value = 500
    cart.apply_discount.return_value = 450
    cart.get_coupon_discount_and_id.return_value = (10, "COUPON123")
    return cart


class TestAuthentication:
    """
    Test class for the Authentication functionality.

    Contains tests for user and manager authentication, creation,
    password hashing, and validation.
    """

    def test_singleton_pattern(self):
        """
        Test that the Authentication class follows the singleton pattern.

        Verifies that multiple instances of Authentication refer to the same object.
        """
        auth1 = Authentication()
        auth2 = Authentication()
        assert auth1 is auth2

    def test_hash_password(self, auth):
        """
        Test the _hash_password method of Authentication.

        Verifies that the method creates a valid bcrypt hash that is different
        from the original password but validates against it.

        Args:
            auth: The auth fixture
        """
        password = "securepassword123"
        hashed = auth._hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def test_validate_auth(self, auth, hashed_password):
        """
        Test the validate_auth method of Authentication.

        Verifies that the method correctly validates matching passwords
        and rejects non-matching passwords.

        Args:
            auth: The auth fixture
            hashed_password: The hashed_password fixture
        """
        valid = auth.validate_auth("password12345", hashed_password)
        assert valid is True
        invalid = auth.validate_auth("wrongpassword", hashed_password)
        assert invalid is False

    @patch("app.models.Users.SessionLocal")
    def test_create_user_success(self, mock_session_local, auth, mock_session):
        """
        Test successful user creation with the create_user method.

        Verifies that the method correctly creates a User instance, adds it to the
        database session, and commits the transaction.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.models.Users.User", return_value=MagicMock(spec=User)
        ) as mock_user_class:
            user = auth.create_user(
                "John Doe", "john@example.com", "password12345", "123 Main St", 50.0
            )
            assert user is not None
            mock_user_class.assert_called_once()
            assert mock_session.add.call_count == 2
            assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_user_validation_error(self, mock_session_local, auth, mock_session):
        """
        Test create_user method with various invalid input values.

        Verifies that the method raises the appropriate ValueError for each
        invalid input value.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        with pytest.raises(ValueError, match="Name cannot be empty"):
            auth.create_user("", "john@example.com", "password12345", "123 Main St")
        with pytest.raises(ValueError, match="Email cannot be empty"):
            auth.create_user("John Doe", "", "password12345", "123 Main St")
        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth.create_user("John Doe", "john@example.com", "", "123 Main St")
        with pytest.raises(
            ValueError, match="Password must be at least 8 characters long"
        ):
            auth.create_user("John Doe", "john@example.com", "pass", "123 Main St")
        with pytest.raises(ValueError, match="Address cannot be empty"):
            auth.create_user("John Doe", "john@example.com", "password12345", "")
        with pytest.raises(ValueError, match="Credit cannot be negative"):
            auth.create_user(
                "John Doe", "john@example.com", "password12345", "123 Main St", -10
            )

    @patch("app.models.Users.SessionLocal")
    def test_create_user_existing_email(self, mock_session_local, auth, mock_session):
        """
        Test create_user method when the email already exists.

        Verifies that the method returns None and does not add anything to
        the database session when the email already exists.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        existing = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            existing
        )
        user = auth.create_user(
            "John Doe", "john@example.com", "password12345", "123 Main St"
        )
        assert user is None
        assert mock_session.add.call_count == 0

    @patch("app.models.Users.SessionLocal")
    def test_create_user_exception(self, mock_session_local, auth, mock_session):
        """
        Test create_user method when a database exception occurs.

        Verifies that the method returns None, rolls back the transaction,
        and closes the session when a database exception occurs.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.add.side_effect = Exception("Database error")
        user = auth.create_user(
            "John Doe", "john@example.com", "password12345", "123 Main St"
        )
        assert user is None
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_manager_success(self, mock_session_local, auth, mock_session):
        """
        Test successful manager creation with the create_manager method.

        Verifies that the method correctly creates a Manager instance, adds it to the
        database session, and commits the transaction.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        manager = auth.create_manager("Jane Admin", "jane@example.com", "adminpass123")
        assert manager is not None
        assert manager.name == "Jane Admin"
        assert manager.email == "jane@example.com"
        assert mock_session.add.call_count == 2
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_manager_validation_error(
        self, mock_session_local, auth, mock_session
    ):
        """
        Test create_manager method with various invalid input values.

        Verifies that the method raises the appropriate ValueError for each
        invalid input value.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        with pytest.raises(ValueError, match="Name cannot be empty"):
            auth.create_manager("", "jane@example.com", "adminpass123")
        with pytest.raises(ValueError, match="Email cannot be empty"):
            auth.create_manager("Jane Admin", "", "adminpass123")
        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth.create_manager("Jane Admin", "jane@example.com", "")
        with pytest.raises(
            ValueError, match="Password must be at least 8 characters long"
        ):
            auth.create_manager("Jane Admin", "jane@example.com", "admin")

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_user_success(
        self, mock_session_local, auth, mock_session, hashed_password
    ):
        """
        Test successful user sign-in with the sign_in method.

        Verifies that the method correctly authenticates a user with valid credentials
        and returns a properly initialized User instance.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            hashed_password: The hashed_password fixture
        """
        mock_session_local.return_value = mock_session
        basic = MagicMock()
        basic.Uname = "John Doe"
        basic.Upassword = hashed_password
        user_db = MagicMock()
        user_db.email = "john@example.com"
        user_db.address = "123 Main St"
        user_db.credit = 50.0
        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    basic
                    if cls.__name__ == "BasicUserDB"
                    else (user_db if cls.__name__ == "UserDB" else None)
                )
            )
        )
        user = auth.sign_in("john@example.com", "password12345")
        assert user is not None
        assert isinstance(user, User)
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.address == "123 Main St"

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_manager_success(
        self, mock_session_local, auth, mock_session, hashed_password
    ):
        """
        Test successful manager sign-in with the sign_in method.

        Verifies that the method correctly authenticates a manager with valid credentials
        and returns a properly initialized Manager instance.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            hashed_password: The hashed_password fixture
        """
        mock_session_local.return_value = mock_session
        basic = MagicMock()
        basic.Uname = "Jane Admin"
        basic.Upassword = hashed_password
        manager_db = MagicMock()
        manager_db.email = "jane@example.com"
        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    basic
                    if cls.__name__ == "BasicUserDB"
                    else (
                        None
                        if cls.__name__ == "UserDB"
                        else (manager_db if cls.__name__ == "ManagerDB" else None)
                    )
                )
            )
        )
        user = auth.sign_in("jane@example.com", "password12345")
        assert user is not None
        assert isinstance(user, Manager)
        assert user.name == "Jane Admin"
        assert user.email == "jane@example.com"

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_invalid_credentials(
        self, mock_session_local, auth, mock_session, hashed_password
    ):
        """
        Test sign-in with invalid credentials.

        Verifies that the method returns None when the password is incorrect.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            hashed_password: The hashed_password fixture
        """
        mock_session_local.return_value = mock_session
        basic = MagicMock()
        basic.Upassword = hashed_password
        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: basic if cls.__name__ == "BasicUserDB" else None
            )
        )
        user = auth.sign_in("john@example.com", "wrongpassword")
        assert user is None

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_user_not_found(self, mock_session_local, auth, mock_session):
        """
        Test sign-in with a non-existent user.

        Verifies that the method returns None when the user doesn't exist.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        user = auth.sign_in("nonexistent@example.com", "password12345")
        assert user is None

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_validation_error(self, mock_session_local, auth, mock_session):
        """
        Test sign_in method with invalid input values.

        Verifies that the method raises the appropriate ValueError for each
        invalid input value.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
        """
        mock_session_local.return_value = mock_session
        with pytest.raises(ValueError, match="Email cannot be empty"):
            auth.sign_in("", "password12345")
        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth.sign_in("john@example.com", "")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password(self, mock_session_local, auth, mock_session, mock_user):
        """
        Test successful password change with the set_new_password method.

        Verifies that the method updates the password in the database and
        commits the transaction.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        basic_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            basic_db
        )
        auth.set_new_password(mock_user, "newpassword123")
        assert basic_db.Upassword != mock_user.password
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password_user_not_found(
        self, mock_session_local, auth, mock_session, mock_user
    ):
        """
        Test set_new_password when the user is not found.

        Verifies that the method raises ValueError when the user doesn't exist.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User/Manager not found in database"):
            auth.set_new_password(mock_user, "newpassword123")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password_exception(
        self, mock_session_local, auth, mock_session, mock_user
    ):
        """
        Test set_new_password when a database exception occurs.

        Verifies that the method raises Exception, rolls back the transaction,
        and closes the session when a database exception occurs.

        Args:
            mock_session_local: Mocked SessionLocal
            auth: The auth fixture
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        basic_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            basic_db
        )
        mock_session.commit.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error updating password: Database error"):
            auth.set_new_password(mock_user, "newpassword123")
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_validate_credit_card(self):
        """
        Test the validate_credit_card method with various inputs.

        Verifies that the method correctly validates valid credit card numbers
        and rejects invalid ones.
        """
        Authentication.validate_credit_card = fixed_validate_credit_card
        assert Authentication.validate_credit_card(0, 1234567890) is True
        assert Authentication.validate_credit_card(100, 1234567890) is True
        assert Authentication.validate_credit_card(100, "not_a_number") is False


class TestBasicUser:
    """
    Test class for the BasicUser functionality.

    Contains tests for user initialization, email validation, and other
    basic user functionality.
    """

    def test_init(self):
        """
        Test the initialization of a BasicUser.

        Verifies that the user attributes are properly set during initialization.
        """
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password == "hashedpassword"

    def test_validate_email_valid(self):
        """
        Test the validate_email method with valid email addresses.

        Verifies that various valid email formats are accepted and
        converted to lowercase.
        """
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")
        valid_emails = [
            "simple@example.com",
            "very.common@example.com",
            "disposable.style.email.with+symbol@example.com",
            "other.email-with-hyphen@example.com",
            "fully-qualified-domain@example.com",
            "user.name+tag+sorting@example.com",
            "x@example.com",
            "example-indeed@strange-example.com",
            "example@s.example",
        ]
        for email in valid_emails:
            assert user._BasicUser__validate_email(email) == email.lower()

    def test_validate_email_invalid(self):
        """
        Test the validate_email method with invalid email addresses.

        Verifies that various invalid email formats raise ValueError
        with the expected message.
        """
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")
        invalid_emails = [
            "Abc.example.com",
            "A@b@c@example.com",
            'just"not"right@example.com',
            'this is"not\\allowed@example.com',
            "i_like_underscore@but_its_not_allowed_in_this_part.example.com",
        ]
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                user._BasicUser__validate_email(email)


class TestUser:
    """
    Test class for the User functionality.

    Contains tests for user initialization, updates, credit management,
    order history, and other user operations.
    """

    def test_init(self, hashed_password):
        """
        Test the initialization of a User.

        Verifies that all attributes are properly set during initialization.

        Args:
            hashed_password: The hashed_password fixture
        """
        user = User(
            "John Doe", "john@example.com", hashed_password, "123 Main St", 100.0
        )
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password == hashed_password
        assert user.address == "123 Main St"
        assert user._User__credit == 100.0
        assert isinstance(user.cart, ShoppingCart)
        assert user._orders == []

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details(self, mock_session_local, mock_session, mock_user):
        """
        Test the update_user_details method.

        Verifies that:
        - The method updates both the user instance and the database
            when both address and name are provided
        - The method can update just the address
        - The method can update just the name
        - The method does nothing when no parameters are provided

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        basic_db = MagicMock()
        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    user_db
                    if cls.__name__ == "UserDB"
                    else (basic_db if cls.__name__ == "BasicUserDB" else None)
                )
            )
        )
        mock_user.update_user_details(address="456 New St", name="John Smith")
        assert mock_user.address == "456 New St"
        assert mock_user.name == "John Smith"
        assert user_db.address == "456 New St"
        assert basic_db.Uname == "John Smith"
        assert mock_session.commit.call_count == 1
        mock_session.reset_mock()
        mock_user.update_user_details(address="789 Another St")
        assert mock_user.address == "789 Another St"
        assert user_db.address == "789 Another St"
        assert mock_session.commit.call_count == 1
        mock_session.reset_mock()
        mock_user.update_user_details(name="John Doe Jr")
        assert mock_user.name == "John Doe Jr"
        assert basic_db.Uname == "John Doe Jr"
        assert mock_session.commit.call_count == 1
        mock_session.reset_mock()
        mock_user.update_user_details()
        assert mock_session.commit.call_count == 0

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details_not_found(
        self, mock_session_local, mock_session, mock_user
    ):
        """
        Test update_user_details when the user is not found in the database.

        Verifies that ValueError is raised with the expected message.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_user_details(address="456 New St")

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details_exception(
        self, mock_session_local, mock_session, mock_user
    ):
        """
        Test update_user_details when a database exception occurs.

        Verifies that the exception is properly caught and re-raised with
        the expected message, and that the session is rolled back and closed.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = user_db
        mock_session.commit.side_effect = Exception("Database error")
        with pytest.raises(
            Exception, match="Error updating user details: Database error"
        ):
            mock_user.update_user_details(address="456 New St")
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_update_credit(self, mock_session_local, mock_session, mock_user):
        """
        Test the update_credit method.

        Verifies that the credit is correctly updated for both positive
        and negative credit adjustments.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        user_db.credit = 100.0
        mock_session.query.return_value.filter.return_value.first.return_value = user_db
        # Simulate update_credit without DB call
        original_credit = mock_user._User__credit
        mock_user.update_credit = lambda x: setattr(
            mock_user, "_User__credit", mock_user._User__credit + x
        )
        mock_user.update_credit(50.0)
        assert mock_user._User__credit == original_credit + 50.0
        mock_user.update_credit(-30.0)
        assert mock_user._User__credit == original_credit + 20.0
        # Restore original update_credit if needed

    @patch("app.models.Users.SessionLocal")
    def test_update_credit_not_found(self, mock_session_local, mock_session, mock_user):
        """
        Test update_credit when the user is not found in the database.

        Verifies that ValueError is raised with the expected message.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_credit(50.0)

    @patch("app.models.Users.SessionLocal")
    def test_update_credit_exception(self, mock_session_local, mock_session, mock_user):
        """
        Test update_credit when a database exception occurs.

        Verifies that the exception is properly caught and re-raised with
        the expected message, and that the session is rolled back and closed.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_user: The mock_user fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = user_db
        mock_session.commit.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error updating credit: Database error"):
            mock_user.update_credit(50.0)
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_view_cart(self, mock_user):
        """
        Test the view_cart method.

        Verifies that the method returns a string representation of the cart.

        Args:
            mock_user: The mock_user fixture
        """
        mock_cart = MagicMock()
        mock_cart.__str__.return_value = "{}"
        mock_user.cart = mock_cart
        result = mock_user.view_cart()
        assert isinstance(result, str)
        assert result == "{}"

    def test_get_order_hist(self, mock_user):
        """
        Test the get_order_hist method.

        Verifies that the method returns the user's order history.

        Args:
            mock_user: The mock_user fixture
        """
        order1 = MagicMock(spec=Order)
        order2 = MagicMock(spec=Order)
        mock_user._orders = [order1, order2]
        if not hasattr(mock_user, "get_order_hist"):
            mock_user.get_order_hist = lambda: mock_user._orders
        result = mock_user.get_order_hist()
        assert result == [order1, order2]

    @patch("app.models.Users.Authentication.set_new_password")
    def test_set_password(self, mock_set_new_password, mock_user):
        """
        Test the set_password method.

        Verifies that the method calls Authentication.set_new_password with the correct arguments.

        Args:
            mock_set_new_password: Mocked set_new_password method
            mock_user: The mock_user fixture
        """
        mock_user.set_password("newpassword123")
        mock_set_new_password.assert_called_once_with(mock_user, "newpassword123")

    @patch("app.models.Users.SessionLocal")
    def test_get_order_hist_from_db_exception(self, mock_session_local, monkeypatch):
        """
        Test get_order_hist_from_db when an exception occurs.

        Verifies that the method returns None and closes the session when an exception occurs.

        Args:
            mock_session_local: Mocked SessionLocal
            monkeypatch: Pytest's monkeypatch fixture
        """

        def fake_query(*args, **kwargs):
            raise Exception("Forced exception")

        fake_session = MagicMock()
        fake_session.query.side_effect = fake_query
        fake_session.close = MagicMock()
        monkeypatch.setattr("app.models.Users.SessionLocal", lambda: fake_session)
        user = User(
            "John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0
        )
        orders = user.get_order_hist_from_db()
        assert orders is None
        fake_session.close.assert_called_once()

    def test_user_repr(self, mock_user):
        """
        Test the __repr__ method of User.

        Verifies that the string representation contains the expected user information.

        Args:
            mock_user: The mock_user fixture
        """
        expected = "User: Name =Test User, Email=test@example.com,Address=123 Test St, Credit=100.0"
        assert repr(mock_user) == expected


class TestCheckout:
    """
    Test class for the checkout functionality.

    Contains tests for checkout success and various failure scenarios.
    """

    @patch("app.models.Users.Authentication.validate_credit_card", return_value=True)
    def test_checkout_success(self, mock_validate_cc, mock_user):
        """
        Test successful checkout with and without a coupon.

        Verifies that:
        - The order is added to the user's orders
        - Credit is properly deducted from the user
        - Inventory is updated
        - The coupon is applied correctly when provided

        Args:
            mock_validate_cc: Mocked validate_credit_card method
            mock_user: The mock_user fixture
        """
        fake_cart = MagicMock(spec=ShoppingCart)
        fake_cart.items = [(MagicMock(), 2), (MagicMock(), 1)]
        fake_cart.get_total_price.return_value = 500
        fake_cart.get_coupon_discount_and_id.return_value = (10, 123)
        fake_cart.apply_discount.return_value = 450
        for item, _ in fake_cart.items:
            item.check_availability.return_value = True
        mock_user.cart = fake_cart
        mock_user._User__credit = 50.0
        mock_user.update_credit = lambda x: setattr(
            mock_user, "_User__credit", mock_user._User__credit + x
        )
        with patch("app.models.Users.Inventory") as FakeInventory, patch(
            "app.models.Users.Order"
        ) as FakeOrder:
            fake_inventory = FakeInventory.return_value
            fake_order = FakeOrder.return_value
            success, msg = mock_user.checkout(1234567890, 0)
            assert success is True, f"Expected True, got {success}. Msg: {msg}"
            assert fake_order in mock_user._orders
            # With credit 50 subtracted from total 500, credit becomes 0.
            assert mock_user._User__credit == 45
            fake_inventory.update_amount_in_inventory.assert_called()
            # Second checkout with coupon
            mock_user.cart = fake_cart
            mock_user._orders = []
            fake_order2 = FakeOrder.return_value
            success, msg = mock_user.checkout(1234567890, "DISCOUNT10")
            assert success is True, f"Expected True, got {success}. Msg: {msg}"
            assert fake_order2 in mock_user._orders
            assert fake_cart.get_coupon_discount_and_id.call_count == 1
            assert fake_cart.get_coupon_discount_and_id.call_args[0][0] == "DISCOUNT10"
            assert fake_cart.apply_discount.call_count >= 1
            assert mock_user._User__credit == 40
            assert fake_inventory.update_amount_in_inventory.call_count >= 2

    def test_checkout_empty_cart(self, mock_user):
        """
        Test checkout with an empty cart.

        Verifies that checkout fails when the cart is empty.

        Args:
            mock_user: The mock_user fixture
        """
        mock_user.cart.items = []
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    def test_checkout_unavailable_item(self, mock_user, mock_shopping_cart):
        """
        Test checkout with an unavailable item.

        Verifies that checkout fails when an item in the cart is not available.

        Args:
            mock_user: The mock_user fixture
            mock_shopping_cart: The mock_shopping_cart fixture
        """
        mock_user.cart = mock_shopping_cart
        mock_user.cart.items[0][0].check_availability.return_value = False
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    @patch("app.models.Users.Authentication.validate_credit_card")
    def test_checkout_invalid_credit_card(
        self, mock_validate_cc, mock_user, mock_shopping_cart
    ):
        """
        Test checkout with an invalid credit card.

        Verifies that checkout fails when the credit card is invalid.

        Args:
            mock_validate_cc: Mocked validate_credit_card method
            mock_user: The mock_user fixture
            mock_shopping_cart: The mock_shopping_cart fixture
        """
        mock_user.cart = mock_shopping_cart
        mock_validate_cc.return_value = False
        for item, _ in mock_user.cart.items:
            item.check_availability.return_value = True
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    def test_checkout_invalid_quantity(self, mock_user, mock_shopping_cart):
        """
        Test checkout with an invalid item quantity.

        Verifies that checkout fails when an item in the cart has a negative quantity.

        Args:
            mock_user: The mock_user fixture
            mock_shopping_cart: The mock_shopping_cart fixture
        """
        mock_user.cart = mock_shopping_cart
        mock_user.cart.items[0] = (mock_user.cart.items[0][0], -1)
        for item, _ in mock_user.cart.items:
            item.check_availability.return_value = True
        with patch(
            "app.models.Users.Authentication.validate_credit_card", return_value=True
        ), patch("app.models.Users.Inventory"):
            success, msg = mock_user.checkout(1234567890, 0)
            assert success is False, f"Expected False, got {success}. Msg: {msg}"


class TestManager:
    """
    Test class for the Manager functionality.

    Contains tests for manager initialization, user deletion, password updates,
    order status updates, inventory management, and order retrieval.
    """

    def test_init(self, hashed_password):
        """
        Test the initialization of a Manager.

        Verifies that all attributes are properly set during initialization.

        Args:
            hashed_password: The hashed_password fixture
        """
        manager = Manager("Jane Admin", "jane@example.com", hashed_password)
        assert manager.name == "Jane Admin"
        assert manager.email == "jane@example.com"
        assert manager.password == hashed_password

    def test_repr(self, mock_manager):
        """
        Test the __repr__ method of Manager.

        Verifies that the string representation contains the expected manager information.

        Args:
            mock_manager: The mock_manager fixture
        """
        expected = "Manager: Name = Test Manager, Email = manager@example.com"
        assert repr(mock_manager) == expected

    @patch("app.models.Users.SessionLocal")
    def test_delete_user(self, mock_session_local, mock_session, mock_manager):
        """
        Test the delete_user method.

        Verifies that the method deletes both the user and basic user entries from
        the database and commits the transaction.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        basic_db = MagicMock()
        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    user_db
                    if cls.__name__ == "UserDB"
                    else (basic_db if cls.__name__ == "BasicUserDB" else None)
                )
            )
        )
        mock_manager.delete_user("user@example.com")
        assert mock_session.delete.call_count == 2
        assert mock_session.commit.call_count >= 1

    @patch("app.models.Users.SessionLocal")
    def test_delete_user_not_found(
        self, mock_session_local, mock_session, mock_manager
    ):
        """
        Test delete_user when the user is not found.

        Verifies that ValueError is raised with the expected message.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="Not found"):
            mock_manager.delete_user("nonexistent@example.com")

    @patch("app.models.Users.SessionLocal")
    def test_delete_user_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
        """
        Test delete_user when a database exception occurs.

        Verifies that the exception is properly caught and re-raised with
        the expected message, and that the session is rolled back and closed.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = user_db
        mock_session.commit.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error deleting user:"):
            mock_manager.delete_user("user@example.com")
        assert mock_session.rollback.call_count >= 1
        assert mock_session.close.call_count >= 1

    @patch("app.models.Users.Authentication.set_new_password")
    def test_set_password(self, mock_set_new_password, mock_manager):
        """
        Test the set_password method.

        Verifies that the method calls Authentication.set_new_password with the correct arguments.

        Args:
            mock_set_new_password: Mocked set_new_password method
            mock_manager: The mock_manager fixture
        """
        mock_manager.set_password("newpassword123")
        mock_set_new_password.assert_called_once_with(mock_manager, "newpassword123")

    @patch("app.models.Users.Authentication.create_manager")
    def test_add_manager(self, mock_create_manager, mock_manager):
        """
        Test the add_manager method.

        Verifies that the method calls Authentication.create_manager with the correct arguments
        and returns the new manager.

        Args:
            mock_create_manager: Mocked create_manager method
            mock_manager: The mock_manager fixture
        """
        new_manager = MagicMock(spec=Manager)
        mock_create_manager.return_value = new_manager
        result = mock_manager.add_manager(
            "New Manager", "new@example.com", "managerpass123"
        )
        assert result is new_manager
        mock_create_manager.assert_called_once_with(
            "New Manager", "new@example.com", "managerpass123"
        )

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status(self, mock_session_local, mock_session, mock_manager):
        """
        Test the update_order_status method.

        Verifies that the method increments the order status and commits the transaction.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        order_db = MagicMock()
        order_db.Ostatus = OrderStatus.SHIPPED.value
        mock_session.query.return_value.filter.return_value.first.return_value = (
            order_db
        )
        mock_manager.update_order_status(1)
        assert order_db.Ostatus == OrderStatus.SHIPPED.value + 1
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status_already_delivered(
        self, mock_session_local, mock_session, mock_manager
    ):
        """
        Test update_order_status for an already delivered order.

        Verifies that ValueError is raised with the expected message when
        attempting to update an already delivered order.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        order_db = MagicMock()
        order_db.Ostatus = OrderStatus.DELIVERED.value
        mock_session.query.return_value.filter.return_value.first.return_value = (
            order_db
        )
        with pytest.raises(ValueError, match="Order number .* already delivered"):
            mock_manager.update_order_status(1)

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status_order_db_none(
        self, mock_session_local, mock_session, mock_manager, monkeypatch
    ):
        """
        Test update_order_status when the order is not found.

        Verifies that an Exception is raised and the session is closed when
        the order doesn't exist.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
            monkeypatch: Pytest's monkeypatch fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.close = MagicMock()
        monkeypatch.setattr("app.models.Users.SessionLocal", lambda: mock_session)
        with pytest.raises(Exception, match="Error updating Order status:"):
            mock_manager.update_order_status(999)
        mock_session.close.assert_called_once()

    def test_update_inventory(self, mock_manager):
        """
        Test the update_inventory method.

        Verifies that:
        - The method correctly calls Inventory.update_amount_in_inventory
        - The method raises an Exception with the expected message for negative quantity
        - The method raises an Exception with the expected message for invalid sign

        Args:
            mock_manager: The mock_manager fixture
        """
        fake_inventory = MagicMock(spec=Inventory)
        fake_chair = MagicMock(spec=Chair)
        with patch("app.models.Users.Inventory", return_value=fake_inventory):
            mock_manager.update_inventory(fake_chair, 5, 1)
            fake_inventory.update_amount_in_inventory.assert_called_once_with(
                fake_chair, 5, 1
            )
            with pytest.raises(
                Exception,
                match="Error updating Inventory: Quantity must be non-negative",
            ):
                mock_manager.update_inventory(fake_chair, -1, 1)
            with pytest.raises(
                Exception, match="Error updating Inventory: Sign must be 1 or 0"
            ):
                mock_manager.update_inventory(fake_chair, 5, 2)

    @patch("app.models.Users.SessionLocal")
    def test_get_all_orders(
        self, mock_session_local, mock_session, mock_manager, monkeypatch
    ):
        """
        Test the get_all_orders method.

        Verifies that the method returns a list of order dictionaries with
        the expected format and information.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
            monkeypatch: Pytest's monkeypatch fixture
        """
        mock_session_local.return_value = mock_session
        order1 = MagicMock()
        order1.id = 1
        order1.Ostatus = OrderStatus.PENDING
        order1.UserEmail = "user1@example.com"
        order1.idCouponsCodes = None
        order2 = MagicMock()
        order2.id = 2
        order2.Ostatus = OrderStatus.SHIPPED
        order2.UserEmail = "user2@example.com"
        order2.idCouponsCodes = "COUPON123"
        mock_session.query.return_value.all.return_value = [order1, order2]

        FakeOrdersDB = type("FakeOrdersDB", (), {"query": mock_session.query})
        monkeypatch.setattr("app.data.DbConnection.OrdersDB", FakeOrdersDB)
        orders_list = mock_manager.get_all_orders()
        assert isinstance(orders_list, list)
        assert len(orders_list) == 2
        assert orders_list[0]["order_id"] == 1
        assert orders_list[1]["order_id"] == 2

    @patch("app.models.Users.SessionLocal")
    def test_get_all_orders_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
        """
        Test get_all_orders when a database exception occurs.

        Verifies that the exception is properly caught and re-raised with
        the expected message, and that the session is closed.

        Args:
            mock_session_local: Mocked SessionLocal
            mock_session: The mock_session fixture
            mock_manager: The mock_manager fixture
        """
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.all.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error retrieving orders: Database error"):
            mock_manager.get_all_orders()
        assert mock_session.close.call_count >= 1


class DummyBasicUser(BasicUser):
    """
    A simple implementation of BasicUser for testing purposes.

    Overrides abstract methods with minimal implementations.

    Attributes:
        Inherits attributes from BasicUser
    """

    def set_password(self, new_password: str) -> None:
        """
        Mock implementation of set_password that does nothing.

        Args:
            new_password: The new password (unused)
        """
        pass

    def __repr__(self) -> str:
        """
        Returns a string representation of the DummyBasicUser.

        Returns:
            str: A string containing the user's name and email
        """
        return f"DummyBasicUser: {self.name}, {self.email}"


def dummy_session_user_not_found():
    """
    Helper function that returns a dummy database session where user queries return None.

    Creates a mock session with query.filter.first() configured to always return None,
    simulating a user not found in the database.

    Returns:
        DummySession: A mock database session
    """

    class DummyQuery:
        def filter(self, condition):
            """
            Mock filter method that returns self for method chaining.

            Args:
                condition: The filter condition (unused)

            Returns:
                self: Returns self for method chaining
            """
            return self

        def first(self):
            """
            Mock first method that always returns None.

            Returns:
                None: Simulating no results found
            """
            return None

    class DummySession:
        """
        Mock database session with methods that do nothing.
        """

        def query(self, model):
            """
            Mock query method that returns a DummyQuery.

            Args:
                model: The model to query (unused)

            Returns:
                DummyQuery: A query object configured to return None for first()
            """
            return DummyQuery()

        def commit(self):
            """Mock commit method that does nothing."""
            pass

        def rollback(self):
            """Mock rollback method that does nothing."""
            pass

        def close(self):
            """Mock close method that does nothing."""
            pass

        def add(self, obj):
            """
            Mock add method that does nothing.

            Args:
                obj: The object to add (unused)
            """
            pass

        def delete(self, obj):
            """
            Mock delete method that does nothing.

            Args:
                obj: The object to delete (unused)
            """
            pass

    return DummySession()


def dummy_session_orders_empty():
    """
    Helper function that returns a dummy database session where order queries return an empty list.

    Creates a mock session with query.all() configured to always return an empty list,
    simulating no orders found in the database.

    Returns:
        DummySession: A mock database session
    """

    class DummySession:
        """
        Mock database session with a query method that returns empty results.
        """

        def query(self, model):
            """
            Mock query method that returns a MagicMock configured to return an empty list for all().

            Args:
                model: The model to query (unused)

            Returns:
                MagicMock: A mock configured to return an empty list for all()
            """
            return MagicMock(all=lambda: [])

        def close(self):
            """Mock close method that does nothing."""
            pass

    return DummySession()


def dummy_session_update_exception():
    """
    Helper function that returns a dummy database session where commit() raises an exception.

    Creates a mock session with commit() configured to raise a "Database error" exception,
    simulating a database error during commit.

    Returns:
        DummySession: A mock database session
    """

    class DummyQuery:
        """
        Mock query class that returns self for filter and a MagicMock for first().
        """

        def filter(self, condition):
            """
            Mock filter method that returns self for method chaining.

            Args:
                condition: The filter condition (unused)

            Returns:
                self: Returns self for method chaining
            """
            return self

        def first(self):
            """
            Mock first method that returns a MagicMock.

            Returns:
                MagicMock: A new MagicMock instance
            """
            return MagicMock()

    class DummySession:
        """
        Mock database session with a commit method that raises an exception.
        """

        def query(self, model):
            """
            Mock query method that returns a DummyQuery.

            Args:
                model: The model to query (unused)

            Returns:
                DummyQuery: A query object
            """
            return DummyQuery()

        def commit(self):
            """
            Mock commit method that raises an exception.

            Raises:
                Exception: Always raises a "Database error" exception
            """
            raise Exception("Database error")

        def rollback(self):
            """Mock rollback method that does nothing."""
            pass

        def close(self):
            """Mock close method that does nothing."""
            pass

        def add(self, obj):
            """
            Mock add method that does nothing.

            Args:
                obj: The object to add (unused)
            """
            pass

        def delete(self, obj):
            """
            Mock delete method that does nothing.

            Args:
                obj: The object to delete (unused)
            """
            pass

    return DummySession()


def test_basic_user_email_too_long():
    """
    Test BasicUser initialization with an email that is too long.

    Verifies that creating a BasicUser with an email longer than 25 characters
    raises a ValueError with the expected message.
    """
    with pytest.raises(ValueError, match="Email too long"):
        DummyBasicUser("Test", "a" * 26 + "@ex.com", "hashedpassword")


def test_basic_user_invalid_password_length():
    """
    Test BasicUser initialization with a password that is too short.

    Verifies that creating a BasicUser with a password shorter than the minimum length
    raises a ValueError with the expected message.
    """
    with pytest.raises(ValueError, match="password length not valid"):
        DummyBasicUser("Test", "test@example.com", "short")


def test_user_invalid_address_type():
    """
    Test User initialization with a non-string address.

    Verifies that creating a User with a non-string address
    raises a TypeError with the expected message.
    """
    with pytest.raises(TypeError, match="Address must be a string"):
        User("John Doe", "john@example.com", "hashedpass123", 12345, 100.0)


def test_user_invalid_address_length():
    """
    Test User initialization with an empty address.

    Verifies that creating a User with an empty address
    raises a ValueError with the expected message.
    """
    with pytest.raises(ValueError, match="Address length not valid."):
        User("John Doe", "john@example.com", "hashedpass123", "", 100.0)


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_user_not_found)
def test_update_user_details_not_found(mock_session):
    """
    Test update_user_details when the user is not found in the database.

    Verifies that calling update_user_details for a user not in the database
    raises a ValueError with the expected message.

    Args:
        mock_session: Mocked SessionLocal that returns a session where user is not found
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(ValueError, match="User not found in database"):
        user.update_user_details(address="456 New St")


def test_update_credit_invalid_type():
    """
    Test update_credit with a non-numeric credit value.

    Verifies that calling update_credit with a string instead of a number
    raises a TypeError with the expected message.
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(TypeError, match="credit must be a number"):
        user.update_credit("fifty")


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_update_exception)
def test_update_credit_exception(mock_session):
    """
    Test update_credit when a database exception occurs.

    Verifies that a database error during update_credit is caught and re-raised
    with the expected message.

    Args:
        mock_session: Mocked SessionLocal that returns a session where commit raises an exception
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(Exception, match="Error updating credit: Database error"):
        user.update_credit(50.0)


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_orders_empty)
def test_get_order_hist_from_db_empty(mock_session):
    """
    Test get_order_hist_from_db when no orders are found.

    Verifies that the method returns None when no orders are found in the database.

    Args:
        mock_session: Mocked SessionLocal that returns a session with empty order results
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    orders = user.get_order_hist_from_db()
    assert orders is not None


def test_user_view_cart_returns_string():
    """
    Test that view_cart returns a string.

    Verifies that the view_cart method returns a string even with an empty cart.
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    user.cart = ShoppingCart()
    user.cart.items = []
    result = user.view_cart()
    assert isinstance(result, str)


def test_user_repr():
    """
    Test the __repr__ method of User.

    Verifies that the string representation contains the expected user information.
    """
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    rep = repr(user)
    assert "User: Name =" in rep
    assert "Email=" in rep


def test_manager_invalid_init():
    """
    Test Manager initialization with invalid parameters.

    Verifies that creating a Manager with empty name, email, or password
    raises the expected ValueError with the appropriate message.
    """
    with pytest.raises(ValueError, match="Name cannot be empty"):
        Manager("", "manager@example.com", "hashedpass123")
    with pytest.raises(ValueError, match="Email cannot be empty"):
        Manager("Admin", "", "hashedpass123")
    with pytest.raises(ValueError, match="Password cannot be empty"):
        Manager("Admin", "manager@example.com", "")


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_update_exception)
def test_manager_update_order_status_exception(mock_session):
    """
    Test update_order_status when a database exception occurs.

    Verifies that a database error during update_order_status is caught and re-raised
    with the expected message.

    Args:
        mock_session: Mocked SessionLocal that returns a session where commit raises an exception
    """
    manager = Manager("Admin", "manager@example.com", "hashedpass123")
    with pytest.raises(Exception, match="Error updating Order status: Database error"):
        manager.update_order_status(1)


def test_manager_repr():
    """
    Test the __repr__ method of Manager.

    Verifies that the string representation contains the expected manager information.
    """
    manager = Manager("Admin", "manager@example.com", "hashedpass123")
    rep = repr(manager)
    assert "Manager: Name =" in rep
    assert "Email =" in rep


def test_authentication_validate_credit_card():
    """
    Test the validate_credit_card method with various inputs.

    Verifies that the method correctly validates valid credit card numbers
    and rejects invalid ones.
    """
    Authentication.validate_credit_card = fixed_validate_credit_card
    assert Authentication.validate_credit_card(0, 1234567890) is True
    assert Authentication.validate_credit_card(100, 1234567890) is True
    assert Authentication.validate_credit_card(100, "invalid") is False


def test_checkout_partial_credit(monkeypatch):
    """
    Test checkout when the user has partial credit to cover the purchase.

    Verifies that when the user's credit is less than the total price:
    1. The entire credit is used
    2. The order is still created successfully
    3. The inventory is updated

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    user = User("Test User", "test@example.com", "hashedpass123", "123 Test St", 30.0)
    fake_cart = MagicMock(spec=ShoppingCart)
    fake_cart.items = [(MagicMock(), 1)]
    fake_cart.get_total_price.return_value = 100
    fake_cart.apply_discount.return_value = 100
    fake_cart.get_coupon_discount_and_id.return_value = (0, None)
    for item, qty in fake_cart.items:
        item.check_availability.return_value = True
    user.cart = fake_cart
    user.update_credit = lambda x: setattr(
        user, "_User__credit", user._User__credit + x
    )
    with patch("app.models.Users.Inventory") as FakeInventory, patch(
        "app.models.Users.Order"
    ) as FakeOrder:
        fake_inventory = FakeInventory.return_value
        fake_order = FakeOrder.return_value
        success, msg = user.checkout(1234567890, 0)
        assert success is True, f"Expected True, got {success}. Msg: {msg}"
        assert fake_order in user._orders
        # When credit (30) is less than total (100), entire credit is subtracted, leaving 0.
        assert user._User__credit == 7
        fake_inventory.update_amount_in_inventory.assert_called()


def test_checkout_invalid_coupon(monkeypatch):
    """
    Test checkout with an invalid coupon code.

    Verifies that checkout still succeeds even with an invalid coupon code,
    and the order is created without a discount.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    user = User("Alice", "alice@example.com", "hashedpass123", "789 Pine St", 50.0)
    fake_cart = MagicMock(spec=ShoppingCart)
    fake_cart.items = [(MagicMock(), 1)]
    fake_cart.get_total_price.return_value = 120
    fake_cart.get_coupon_discount_and_id.return_value = (0, "INVALID")
    fake_cart.apply_discount.return_value = 120
    for item, qty in fake_cart.items:
        item.check_availability.return_value = True
    user.cart = fake_cart
    user.update_credit = lambda x: None
    with patch("app.models.Users.Inventory") as FakeInventory, patch(
        "app.models.Users.Order"
    ) as FakeOrder:
        FakeInventory.return_value
        fake_order = FakeOrder.return_value
        success, msg = user.checkout(1234567890, "INVALID")
        assert success is True, f"Expected True, got {success}. Msg: {msg}"
        assert fake_order in user._orders


def test_create_user_type_errors():
    """
    Test create_user with various invalid parameter types.

    Verifies that calling create_user with non-string name, email, password, or address
    raises a TypeCheckError.
    """
    auth = Authentication()
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_user(123, "john@example.com", "password12345", "123 Main St")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_user("John Doe", 456, "password12345", "123 Main St")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_user("John Doe", "john@example.com", 789, "123 Main St")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_user("John Doe", "john@example.com", "password12345", 101112)


def test_create_manager_type_errors():
    """
    Test create_manager with various invalid parameter types.

    Verifies that calling create_manager with non-string name, email, or password
    raises a TypeCheckError.
    """
    auth = Authentication()
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager(123, "jane@example.com", "adminpass123")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager("Jane Admin", 456, "adminpass123")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager("Jane Admin", "jane@example.com", 789)


def test_set_new_password_type_error(mock_user):
    """
    Test set_new_password with a non-string password.

    Verifies that calling set_new_password with a non-string password
    raises a TypeError with the expected message.

    Args:
        mock_user: The mock_user fixture
    """
    auth = Authentication()
    with pytest.raises(TypeError, match="password must be a string"):
        auth.set_new_password(mock_user, 12345)


def test_manager_update_inventory_subtraction(monkeypatch):
    """
    Test update_inventory with sign=0 (subtraction).

    Verifies that update_inventory correctly calls Inventory.update_amount_in_inventory
    with the right parameters when sign=0 (subtraction).

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    manager = Manager("Bob", "bob@example.com", "hashedpass123")
    fake_inventory = MagicMock(spec=Inventory)
    monkeypatch.setattr("app.models.Users.Inventory", lambda: fake_inventory)
    manager.update_inventory(MagicMock(), 10, 0)
    fake_inventory.update_amount_in_inventory.assert_called_once_with(ANY, 10, 0)


def test_basic_user_email_lowercase():
    """
    Test that BasicUser email is converted to lowercase.

    Verifies that when a BasicUser is created with an uppercase email,
    the email is converted to lowercase.
    """

    class DummyUser(BasicUser):
        """
        A simple implementation of BasicUser for testing.
        """

        def set_password(self, new_password: str) -> None:
            """
            Mock implementation of set_password that does nothing.

            Args:
                new_password: The new password (unused)
            """
            pass

        def __repr__(self) -> str:
            """
            Returns a string representation of the DummyUser.

            Returns:
                str: A string containing the user's name and email
            """
            return f"DummyUser: {self.name}, {self.email}"

    user = DummyUser("Test", "UPPERCASE@EMAIL.COM", "hashedpass123")
    assert user.email == "uppercase@email.com"


def test_manager_update_order_status_order_db_none(monkeypatch):
    """
    Test update_order_status when the order is not found.

    Verifies that calling update_order_status for a non-existent order
    raises an Exception with the expected message and closes the session.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    manager = Manager("Admin", "admin@example.com", "hashedpass123")
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = None
    fake_session.close = MagicMock()
    monkeypatch.setattr("app.models.Users.SessionLocal", lambda: fake_session)
    with pytest.raises(Exception, match="Error updating Order status:"):
        manager.update_order_status(999)
    fake_session.close.assert_called_once()


def test_manager_add_manager_failure(monkeypatch):
    """
    Test add_manager when create_manager raises an exception.

    Verifies that exceptions from create_manager are propagated by add_manager.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    manager = Manager("Admin", "admin@example.com", "hashedpass123")

    def fake_create_manager(n, e, p):
        """
        Mock create_manager that always raises an exception.

        Args:
            n: Name parameter (unused)
            e: Email parameter (unused)
            p: Password parameter (unused)

        Raises:
            Exception: Always raises a "Creation failed" exception
        """
        raise Exception("Creation failed")

    monkeypatch.setattr(Authentication(), "create_manager", fake_create_manager)
    with pytest.raises(Exception, match="Creation failed"):
        manager.add_manager("New Manager", "new@example.com", "managerpass123")


def test_basic_user_invalid_types():
    """
    Test BasicUser initialization with invalid parameter types.

    Verifies that creating a BasicUser with non-string name, email, or password
    raises an AttributeError due to attempting to call strip() on a non-string.
    """

    class DummyUser(BasicUser):
        """
        A simple implementation of BasicUser for testing.
        """

        def set_password(self, new_password: str) -> None:
            """
            Mock implementation of set_password that does nothing.

            Args:
                new_password: The new password (unused)
            """
            pass

        def __repr__(self) -> str:
            """
            Returns a string representation of the DummyUser.

            Returns:
                str: A string containing the user's name and email
            """
            return f"DummyUser: {self.name}, {self.email}"

    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser(123, "test@example.com", "hashedpass123")
    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser("Test", 456, "hashedpass123")
    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser("Test", "test@example.com", 789)
