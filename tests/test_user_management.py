import pytest
import bcrypt
from unittest.mock import patch, MagicMock

# Import the module to be tested
from app.models.Users import Authentication, BasicUser, User, Manager
from app.models.ShoppingCart import ShoppingCart
from app.models.EnumsClass import OrderStatus
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.FurnituresClass import Chair, Table


class MockBasicUser(BasicUser):
    """Mock implementation of BasicUser for testing abstract methods"""

    def set_password(self, new_password):
        pass

    def __repr__(self):
        return f"MockBasicUser: {self.name}, {self.email}"


# Fixtures for common objects
@pytest.fixture
def mock_session():
    """Create a mock database session"""
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
    """Create an Authentication instance"""
    return Authentication()


@pytest.fixture
def hashed_password():
    """Create a real hashed password for testing"""
    return bcrypt.hashpw("password12345".encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


@pytest.fixture
def mock_user(hashed_password):
    """Create a mock user for testing"""
    return User("Test User", "test@example.com", hashed_password, "123 Test St", 100.0)


@pytest.fixture
def mock_manager(hashed_password):
    """Create a mock manager for testing"""
    return Manager("Test Manager", "manager@example.com", hashed_password)


@pytest.fixture
def mock_shopping_cart():
    """Create a mock shopping cart"""
    cart = MagicMock(spec=ShoppingCart)
    cart.items = [(MagicMock(spec=Chair), 2), (MagicMock(spec=Table), 1)]
    cart.get_total_price.return_value = 500
    cart.apply_discount.return_value = 450
    cart.get_coupon_discount_and_id.return_value = (10, "COUPON123")
    return cart


# Test for Authentication class
class TestAuthentication:
    def test_singleton_pattern(self):
        """Test that Authentication is a singleton"""
        auth1 = Authentication()
        auth2 = Authentication()
        assert auth1 is auth2

    def test_hash_password(self, auth):
        """Test that password hashing works"""
        password = "securepassword123"
        hashed = auth._hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def test_validate_auth(self, auth, hashed_password):
        """Test password validation"""
        valid = auth.validate_auth("password12345", hashed_password)
        assert valid is True

        invalid = auth.validate_auth("wrongpassword", hashed_password)
        assert invalid is False

    @patch("app.models.Users.SessionLocal")
    def test_create_user_success(self, mock_session_local, auth, mock_session):
        """Test creating a user successfully"""
        mock_session_local.return_value = mock_session

        # Configure mock to simulate successful user creation
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.models.Users.User", return_value=MagicMock(spec=User)
        ) as mock_user_class:
            user = auth.create_user(
                "John Doe", "john@example.com", "password12345", "123 Main St", 50.0
            )

            assert user is not None
            mock_user_class.assert_called_once()
            mock_session.add.call_count == 2  # Called for BasicUserDB and UserDB
            mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_user_validation_error(self, mock_session_local, auth, mock_session):
        """Test validation errors during user creation"""
        mock_session_local.return_value = mock_session

        # Test various validation errors
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
        """Test creating a user with an email that already exists"""
        mock_session_local.return_value = mock_session

        # Simulate existing user
        mock_existing_user = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_existing_user
        )

        user = auth.create_user(
            "John Doe", "john@example.com", "password12345", "123 Main St"
        )

        assert user is None
        assert mock_session.add.call_count == 0

    @patch("app.models.Users.SessionLocal")
    def test_create_user_exception(self, mock_session_local, auth, mock_session):
        """Test handling exceptions during user creation"""
        mock_session_local.return_value = mock_session

        # Simulate exception during saving
        mock_session.add.side_effect = Exception("Database error")

        user = auth.create_user(
            "John Doe", "john@example.com", "password12345", "123 Main St"
        )

        assert user is None
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_manager_success(self, mock_session_local, auth, mock_session):
        """Test creating a manager successfully"""
        mock_session_local.return_value = mock_session

        # Configure mock to simulate successful manager creation
        mock_session.query.return_value.filter.return_value.first.return_value = None

        manager = auth.create_manager("Jane Admin", "jane@example.com", "adminpass123")

        assert manager is not None
        assert manager.name == "Jane Admin"
        assert manager.email == "jane@example.com"
        assert mock_session.add.call_count == 2  # Called for BasicUserDB and ManagerDB
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_create_manager_validation_error(
        self, mock_session_local, auth, mock_session
    ):
        """Test validation errors during manager creation"""
        mock_session_local.return_value = mock_session

        # Test various validation errors
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
        """Test signing in as a user successfully"""
        mock_session_local.return_value = mock_session

        # Set up mocks for successful user sign in
        mock_basic_user = MagicMock()
        mock_basic_user.Uname = "John Doe"
        mock_basic_user.Upassword = hashed_password

        mock_user = MagicMock()
        mock_user.email = "john@example.com"
        mock_user.address = "123 Main St"
        mock_user._User__credit = 50.0

        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    mock_basic_user
                    if cls.__name__ == "BasicUserDB"
                    else (mock_user if cls.__name__ == "UserDB" else None)
                )
            )
        )

        user = auth.sign_in("john@example.com", "password12345")

        assert user is not None
        assert isinstance(user, User)
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.address == "123 Main St"
        assert user.credit == 50.0

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_manager_success(
        self, mock_session_local, auth, mock_session, hashed_password
    ):
        """Test signing in as a manager successfully"""
        mock_session_local.return_value = mock_session

        # Set up mocks for successful manager sign in
        mock_basic_user = MagicMock()
        mock_basic_user.Uname = "Jane Admin"
        mock_basic_user.Upassword = hashed_password

        mock_manager = MagicMock()
        mock_manager.email = "jane@example.com"

        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    mock_basic_user
                    if cls.__name__ == "BasicUserDB"
                    else (
                        None
                        if cls.__name__ == "UserDB"
                        else mock_manager if cls.__name__ == "ManagerDB" else None
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
        """Test signing in with invalid credentials"""
        mock_session_local.return_value = mock_session

        # Set up mocks for invalid sign in
        mock_basic_user = MagicMock()
        mock_basic_user.Upassword = hashed_password

        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: mock_basic_user if cls.__name__ == "BasicUserDB" else None
            )
        )

        user = auth.sign_in("john@example.com", "wrongpassword")

        assert user is None

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_user_not_found(self, mock_session_local, auth, mock_session):
        """Test signing in with an email that doesn't exist"""
        mock_session_local.return_value = mock_session

        # No user found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        user = auth.sign_in("nonexistent@example.com", "password12345")

        assert user is None

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_validation_error(self, mock_session_local, auth, mock_session):
        """Test validation errors during sign in"""
        mock_session_local.return_value = mock_session

        with pytest.raises(ValueError, match="Email cannot be empty"):
            auth.sign_in("", "password12345")

        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth.sign_in("john@example.com", "")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password(self, mock_session_local, auth, mock_session, mock_user):
        """Test setting a new password"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_basic_user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_basic_user_db
        )

        auth.set_new_password(mock_user, "newpassword123")

        # Check that the password was updated
        assert mock_basic_user_db.Upassword != mock_user.password
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password_user_not_found(
        self, mock_session_local, auth, mock_session, mock_user
    ):
        """Test setting a password for a user that doesn't exist"""
        mock_session_local.return_value = mock_session

        # No user found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="User/Manager not found in database"):
            auth.set_new_password(mock_user, "newpassword123")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password_exception(
        self, mock_session_local, auth, mock_session, mock_user
    ):
        """Test handling exceptions when setting a new password"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_basic_user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_basic_user_db
        )

        # Simulate exception during saving
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error updating password"):
            auth.set_new_password(mock_user, "newpassword123")

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_validate_credit_card(self):
        """Test credit card validation"""
        # Valid scenarios
        assert Authentication.validate_credit_card(0, 1234567890) is True
        assert Authentication.validate_credit_card(100, 1234567890) is True

        # Invalid scenarios
        assert Authentication.validate_credit_card(100, "not_a_number") is False


# Test for BasicUser class
class TestBasicUser:
    def test_init(self):
        """Test initialization of a BasicUser"""
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")

        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password == "hashedpassword"

    def test_validate_email_valid(self):
        """Test validation of valid email addresses"""
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
        """Test validation of invalid email addresses"""
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")

        invalid_emails = [
            "Abc.example.com",  # No @ character
            "A@b@c@example.com",  # Multiple @ characters
            'just"not"right@example.com',  # Quoted strings
            'this is"not\\allowed@example.com',  # Spaces
            "i_like_underscore@but_its_not_allowed_in_this_part.example.com",  # _ in domain
        ]

        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                user._BasicUser__validate_email(email)


# Test for User class
class TestUser:
    def test_init(self, hashed_password):
        """Test initialization of a User"""
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
        """Test updating user details"""
        mock_session_local.return_value = mock_session

        # Set up mocks for database entities
        mock_user_db = MagicMock()
        mock_basic_user_db = MagicMock()

        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    mock_user_db
                    if cls.__name__ == "UserDB"
                    else mock_basic_user_db if cls.__name__ == "BasicUserDB" else None
                )
            )
        )

        # Test updating both name and address
        mock_user.update_user_details(address="456 New St", name="John Smith")

        assert mock_user.address == "456 New St"
        assert mock_user.name == "John Smith"
        assert mock_user_db.address == "456 New St"
        assert mock_basic_user_db.Uname == "John Smith"
        assert mock_session.commit.call_count == 1

        # Test updating just address
        mock_session.reset_mock()
        mock_user.update_user_details(address="789 Another St")

        assert mock_user.address == "789 Another St"
        assert mock_user_db.address == "789 Another St"
        assert mock_session.commit.call_count == 1

        # Test updating just name
        mock_session.reset_mock()
        mock_user.update_user_details(name="John Doe Jr")

        assert mock_user.name == "John Doe Jr"
        assert mock_basic_user_db.Uname == "John Doe Jr"
        assert mock_session.commit.call_count == 1

        # Test with no updates
        mock_session.reset_mock()
        mock_user.update_user_details()

        assert mock_session.commit.call_count == 0

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details_not_found(
        self, mock_session_local, mock_session, mock_user
    ):
        """Test updating details for a user that doesn't exist"""
        mock_session_local.return_value = mock_session

        # No user found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_user_details(address="456 New St")

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details_exception(
        self, mock_session_local, mock_session, mock_user
    ):
        """Test handling exceptions when updating user details"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_user_db
        )

        # Simulate exception during saving
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error updating user details"):
            mock_user.update_user_details(address="456 New St")

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_update_credit(self, mock_session_local, mock_session, mock_user):
        """Test updating user credit"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_user_db = MagicMock()
        mock_user_db.credit = 100.0
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_user_db
        )

        # Add credit
        mock_user.update_credit(50.0)

        assert mock_user_db.credit == 150.0
        assert mock_user._User__credit == 150.0
        assert mock_session.commit.call_count == 1

        # Subtract credit
        mock_session.reset_mock()
        mock_user_db.credit = 150.0

        mock_user.update_credit(-30.0)

        assert mock_user_db.credit == 120.0
        assert mock_user._User__credit == 120.0
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_update_credit_not_found(self, mock_session_local, mock_session, mock_user):
        """Test updating credit for a user that doesn't exist"""
        mock_session_local.return_value = mock_session

        # No user found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_credit(50.0)

    @patch("app.models.Users.SessionLocal")
    def test_update_credit_exception(self, mock_session_local, mock_session, mock_user):
        """Test handling exceptions when updating credit"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_user_db
        )

        # Simulate exception during saving
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error updating credit"):
            mock_user.update_credit(50.0)

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_view_cart(self, mock_user):
        """Test viewing the shopping cart"""
        # Mock the cart's __str__ method
        mock_cart = MagicMock()
        mock_cart.__str__.return_value = "Cart with 3 items"

        # Replace the user's cart with our mock
        mock_user.cart = mock_cart

        result = mock_user.view_cart()
        assert result == "Cart with 3 items"
        assert mock_user.cart.__str__.call_count == 1

    def test_get_order_hist(self, mock_user):
        """Test getting order history"""
        # Add some orders
        mock_order1 = MagicMock(spec=Order)
        mock_order2 = MagicMock(spec=Order)
        mock_user._orders = [mock_order1, mock_order2]

        result = mock_user.get_order_hist()

        assert result == [mock_order1, mock_order2]

    @patch("app.models.Users.Authentication.set_new_password")
    def test_set_password(self, mock_set_new_password, mock_user):
        """Test setting a new password"""
        mock_user.set_password("newpassword123")

        mock_set_new_password.assert_called_once_with(mock_user, "newpassword123")

    @patch("app.models.Users.Authentication.validate_credit_card", return_value=True)
    def test_checkout_success(self, mock_validate_cc, mock_user):
        """Test successful checkout"""
        # Create a properly configured cart mock
        mock_cart = MagicMock()
        mock_cart.items = [(MagicMock(), 2), (MagicMock(), 1)]
        mock_cart.get_total_price.return_value = 500

        # Setup coupon handling
        mock_cart.get_coupon_discount_and_id.return_value = (10, 123)
        mock_cart.apply_discount.return_value = 450

        # Make sure the items pass availability check
        for item, _ in mock_cart.items:
            item.check_availability.return_value = True

        # Replace user's cart and set up credit
        mock_user.cart = mock_cart
        mock_user._User__credit = 50.0
        mock_user.update_credit = MagicMock()

        # Mock inventory
        mock_inventory = MagicMock()
        with patch("app.models.Users.Inventory", return_value=mock_inventory):
            # Mock Order creation to return a specific mock we can track
            mock_order = MagicMock()
            with patch("app.models.Users.Order", return_value=mock_order):
                # Test basic checkout (no coupon)
                result = mock_user.checkout(1234567890)

                assert result is True
                # Check if order was added to user's orders
                assert mock_order in mock_user._orders
                # Verify credit was used
                assert mock_user.update_credit.call_count == 1
                assert mock_user.update_credit.call_args[0][0] == -50.0
                # Verify inventory was updated for both items
                assert mock_inventory.update_amount_in_inventory.call_count == 2

                # Clear state for the next test
                mock_user._orders = []
                mock_user.update_credit.reset_mock()
                mock_inventory.update_amount_in_inventory.reset_mock()

                # Test checkout with coupon
                mock_order2 = MagicMock()  # Different mock for second order
                with patch("app.models.Users.Order", return_value=mock_order2):
                    result = mock_user.checkout(1234567890, "DISCOUNT10")

                    assert result is True
                    # Check if order was added
                    assert mock_order2 in mock_user._orders
                    # Verify coupon was processed
                    assert mock_cart.get_coupon_discount_and_id.call_count == 1
                    assert (
                        mock_cart.get_coupon_discount_and_id.call_args[0][0]
                        == "DISCOUNT10"
                    )
                    assert mock_cart.apply_discount.call_count == 1
                    # Verify credit was used properly
                    assert mock_user.update_credit.call_count == 1
                    # Verify inventory was updated for all items
                    assert mock_inventory.update_amount_in_inventory.call_count == 2

    def test_checkout_empty_cart(self, mock_user):
        """Test checkout with empty cart"""
        mock_user.cart.items = []

        result = mock_user.checkout(1234567890)

        assert result is False

    def test_checkout_unavailable_item(self, mock_user, mock_shopping_cart):
        """Test checkout with unavailable item"""
        mock_user.cart = mock_shopping_cart

        # One item not available
        mock_user.cart.items[0][0].check_availability.return_value = False

        result = mock_user.checkout(1234567890)

        assert result is False

    @patch("app.models.Users.Authentication.validate_credit_card")
    def test_checkout_invalid_credit_card(
        self, mock_validate_cc, mock_user, mock_shopping_cart
    ):
        """Test checkout with invalid credit card"""
        mock_user.cart = mock_shopping_cart
        mock_validate_cc.return_value = False

        # All items available
        for item, _ in mock_user.cart.items:
            item.check_availability.return_value = True

        result = mock_user.checkout(1234567890)

        assert result is False

    def test_checkout_invalid_quantity(self, mock_user, mock_shopping_cart):
        """Test checkout with invalid item quantity"""
        mock_user.cart = mock_shopping_cart

        # Invalid quantity
        mock_user.cart.items[0] = (mock_user.cart.items[0][0], -1)

        # All items available
        for item, _ in mock_user.cart.items:
            item.check_availability.return_value = True

        with patch(
            "app.models.Users.Authentication.validate_credit_card", return_value=True
        ):
            with patch("app.models.Users.Inventory"):
                result = mock_user.checkout(1234567890)

                assert result is False

    def test_repr(self, mock_user):
        """Test string representation of a User"""
        expected = "User: Name =Test User, Email=test@example.com,Address=123 Test St, Credit=100.0"

        assert repr(mock_user) == expected


# Test for Manager class
class TestManager:
    def test_init(self, hashed_password):
        """Test initialization of a Manager"""
        manager = Manager("Jane Admin", "jane@example.com", hashed_password)

        assert manager.name == "Jane Admin"
        assert manager.email == "jane@example.com"
        assert manager.password == hashed_password

    def test_repr(self, mock_manager):
        """Test string representation of a Manager"""
        expected = "Manager: Name = Test Manager, Email = manager@example.com"

        assert repr(mock_manager) == expected

    @patch("app.models.Users.SessionLocal")
    def test_delete_user(self, mock_session_local, mock_session, mock_manager):
        """Test deleting a user"""
        mock_session_local.return_value = mock_session

        # Set up mocks for database entities
        mock_user_db = MagicMock()
        mock_basic_user_db = MagicMock()

        mock_session.query.side_effect = lambda cls: MagicMock(
            filter=lambda *args: MagicMock(
                first=lambda: (
                    mock_user_db
                    if cls.__name__ == "UserDB"
                    else mock_basic_user_db if cls.__name__ == "BasicUserDB" else None
                )
            )
        )

        mock_manager.delete_user("user@example.com")

        assert mock_session.delete.call_count == 2
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_delete_user_not_found(
        self, mock_session_local, mock_session, mock_manager
    ):
        """Test deleting a user that doesn't exist"""
        mock_session_local.return_value = mock_session

        # No user found
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_manager.delete_user("nonexistent@example.com")

        assert mock_session.delete.call_count == 0
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_delete_user_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
        """Test handling exceptions when deleting a user"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding user
        mock_user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_user_db
        )

        # Simulate exception during delete
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error deleting user"):
            mock_manager.delete_user("user@example.com")

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    @patch("app.models.Users.Authentication.set_new_password")
    def test_set_password(self, mock_set_new_password, mock_manager):
        """Test setting a new password for a manager"""
        mock_manager.set_password("newpassword123")

        mock_set_new_password.assert_called_once_with(mock_manager, "newpassword123")

    @patch("app.models.Users.Authentication.create_manager")
    def test_add_manager(self, mock_create_manager, mock_manager):
        """Test adding a new manager"""
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
        """Test updating order status"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding order
        mock_order_db = MagicMock()
        mock_order_db.id = 1
        mock_order_db.Ostatus = OrderStatus.SHIPPED.value
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_order_db
        )

        mock_manager.update_order_status(1)

        assert mock_order_db.Ostatus == OrderStatus.SHIPPED.value + 1
        assert mock_session.commit.call_count == 1

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status_already_delivered(
        self, mock_session_local, mock_session, mock_manager
    ):
        """Test updating status of an already delivered order"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding order
        mock_order_db = MagicMock()
        mock_order_db.id = OrderStatus.DELIVERED
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_order_db
        )

        with pytest.raises(ValueError, match="Order number .* already delivered"):
            mock_manager.update_order_status(1)

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
        """Test handling exceptions when updating order status"""
        mock_session_local.return_value = mock_session

        # Set up mock for finding order
        mock_order_db = MagicMock()
        mock_order_db.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_order_db
        )

        # Simulate exception during update
        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error updating Order status"):
            mock_manager.update_order_status(1)

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_update_inventory(self, mock_manager):
        """Test updating inventory"""
        # Mock inventory
        mock_inventory = MagicMock(spec=Inventory)

        # Mock furniture items
        mock_chair = MagicMock(spec=Chair)

        with patch("app.models.Users.Inventory", return_value=mock_inventory):
            # Test addition
            mock_manager.update_inventory(mock_chair, 5, 1)

            mock_inventory.update_amount_in_inventory.assert_called_once_with(
                mock_chair, 5, 1
            )

            # Test with invalid quantity
            with pytest.raises(
                Exception,
                match="Error updating Inventory: Quantity must be non-negative",
            ):
                mock_manager.update_inventory(mock_chair, -1, 1)

            # Test with invalid sign
            with pytest.raises(
                Exception, match="Error updating Inventory: Sign must be 1 or 0"
            ):
                mock_manager.update_inventory(mock_chair, 5, 2)

    @patch("app.models.Users.SessionLocal")
    def test_get_all_orders(self, mock_session_local, mock_session, mock_manager):
        """Test getting all orders"""
        mock_session_local.return_value = mock_session

        # Set up mock for orders
        mock_order1 = MagicMock()
        mock_order1.id = 1
        mock_order1.Ostatus = OrderStatus.PENDING
        mock_order1.UserEmail = "user1@example.com"
        mock_order1.idCouponsCodes = None

        mock_order2 = MagicMock()
        mock_order2.id = 2
        mock_order2.Ostatus = OrderStatus.SHIPPED
        mock_order2.UserEmail = "user2@example.com"
        mock_order2.idCouponsCodes = "COUPON123"

        mock_session.query.return_value.all.return_value = [mock_order1, mock_order2]

        # Capture print output
        with patch("builtins.print") as mock_print:
            mock_manager.get_all_orders()

            # Check print was called multiple times for each order
            assert mock_print.call_count >= 10

    @patch("app.models.Users.SessionLocal")
    def test_get_all_orders_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
        """Test handling exceptions when getting all orders"""
        mock_session_local.return_value = mock_session

        # Simulate exception during query
        mock_session.query.return_value.all.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Error retrieving orders"):
            mock_manager.get_all_orders()

        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1
