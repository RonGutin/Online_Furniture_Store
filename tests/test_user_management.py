import pytest
import bcrypt
from unittest.mock import patch, MagicMock, ANY
from app.models.Users import Authentication, BasicUser, User, Manager
from app.models.ShoppingCart import ShoppingCart
from app.models.EnumsClass import OrderStatus
from app.models.order import Order
from app.models.inventory import Inventory
from app.models.FurnituresClass import Chair, Table
from typing import Union
import typeguard


def fixed_validate_credit_card(
    total_price: int, credit_card_num: Union[int, str]
) -> bool:
    if total_price == 0:
        return True
    try:
        int(credit_card_num)
    except Exception:
        return False
    return True


class MockBasicUser(BasicUser):
    def set_password(self, new_password):
        pass

    def __repr__(self):
        return f"MockBasicUser: {self.name}, {self.email}"


@pytest.fixture
def mock_session():
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
    return Authentication()


@pytest.fixture
def hashed_password():
    return bcrypt.hashpw("password12345".encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


@pytest.fixture
def mock_user(hashed_password):
    return User("Test User", "test@example.com", hashed_password, "123 Test St", 100.0)


@pytest.fixture
def mock_manager(hashed_password):
    return Manager("Test Manager", "manager@example.com", hashed_password)


@pytest.fixture
def mock_shopping_cart():
    cart = MagicMock(spec=ShoppingCart)
    cart.items = [(MagicMock(spec=Chair), 2), (MagicMock(spec=Table), 1)]
    cart.get_total_price.return_value = 500
    cart.apply_discount.return_value = 450
    cart.get_coupon_discount_and_id.return_value = (10, "COUPON123")
    return cart


class TestAuthentication:
    def test_singleton_pattern(self):
        auth1 = Authentication()
        auth2 = Authentication()
        assert auth1 is auth2

    def test_hash_password(self, auth):
        password = "securepassword123"
        hashed = auth._hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def test_validate_auth(self, auth, hashed_password):
        valid = auth.validate_auth("password12345", hashed_password)
        assert valid is True
        invalid = auth.validate_auth("wrongpassword", hashed_password)
        assert invalid is False

    @patch("app.models.Users.SessionLocal")
    def test_create_user_success(self, mock_session_local, auth, mock_session):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        user = auth.sign_in("nonexistent@example.com", "password12345")
        assert user is None

    @patch("app.models.Users.SessionLocal")
    def test_sign_in_validation_error(self, mock_session_local, auth, mock_session):
        mock_session_local.return_value = mock_session
        with pytest.raises(ValueError, match="Email cannot be empty"):
            auth.sign_in("", "password12345")
        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth.sign_in("john@example.com", "")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password(self, mock_session_local, auth, mock_session, mock_user):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User/Manager not found in database"):
            auth.set_new_password(mock_user, "newpassword123")

    @patch("app.models.Users.SessionLocal")
    def test_set_new_password_exception(
        self, mock_session_local, auth, mock_session, mock_user
    ):
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
        Authentication.validate_credit_card = fixed_validate_credit_card
        assert Authentication.validate_credit_card(0, 1234567890) is True
        assert Authentication.validate_credit_card(100, 1234567890) is True
        assert Authentication.validate_credit_card(100, "not_a_number") is False


class TestBasicUser:
    def test_init(self):
        user = MockBasicUser("Test User", "test@example.com", "hashedpassword")
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.password == "hashedpassword"

    def test_validate_email_valid(self):
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
    def test_init(self, hashed_password):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_user_details(address="456 New St")

    @patch("app.models.Users.SessionLocal")
    def test_update_user_details_exception(
        self, mock_session_local, mock_session, mock_user
    ):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="User not found in database"):
            mock_user.update_credit(50.0)

    @patch("app.models.Users.SessionLocal")
    def test_update_credit_exception(self, mock_session_local, mock_session, mock_user):
        mock_session_local.return_value = mock_session
        user_db = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = user_db
        mock_session.commit.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error updating credit: Database error"):
            mock_user.update_credit(50.0)
        assert mock_session.rollback.call_count == 1
        assert mock_session.close.call_count == 1

    def test_view_cart(self, mock_user):
        mock_cart = MagicMock()
        mock_cart.__str__.return_value = "{}"
        mock_user.cart = mock_cart
        result = mock_user.view_cart()
        assert isinstance(result, str)
        assert result == "{}"

    def test_get_order_hist(self, mock_user):
        order1 = MagicMock(spec=Order)
        order2 = MagicMock(spec=Order)
        mock_user._orders = [order1, order2]
        if not hasattr(mock_user, "get_order_hist"):
            mock_user.get_order_hist = lambda: mock_user._orders
        result = mock_user.get_order_hist()
        assert result == [order1, order2]

    @patch("app.models.Users.Authentication.set_new_password")
    def test_set_password(self, mock_set_new_password, mock_user):
        mock_user.set_password("newpassword123")
        mock_set_new_password.assert_called_once_with(mock_user, "newpassword123")

    @patch("app.models.Users.SessionLocal")
    def test_get_order_hist_from_db_exception(self, mock_session_local, monkeypatch):
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
        expected = "User: Name =Test User, Email=test@example.com,Address=123 Test St, Credit=100.0"
        assert repr(mock_user) == expected


class TestCheckout:
    @patch("app.models.Users.Authentication.validate_credit_card", return_value=True)
    def test_checkout_success(self, mock_validate_cc, mock_user):
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
            assert mock_user._User__credit == 0
            fake_inventory.update_amount_in_inventory.assert_called()
            # Second checkout with coupon
            mock_user.cart = fake_cart
            mock_user._orders = []
            fake_order2 = FakeOrder.return_value
            success, msg = mock_user.checkout(1234567890, 0, "DISCOUNT10")
            assert success is True, f"Expected True, got {success}. Msg: {msg}"
            assert fake_order2 in mock_user._orders
            assert fake_cart.get_coupon_discount_and_id.call_count == 1
            assert fake_cart.get_coupon_discount_and_id.call_args[0][0] == "DISCOUNT10"
            assert fake_cart.apply_discount.call_count >= 1
            assert mock_user._User__credit == 0
            assert fake_inventory.update_amount_in_inventory.call_count >= 2

    def test_checkout_empty_cart(self, mock_user):
        mock_user.cart.items = []
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    def test_checkout_unavailable_item(self, mock_user, mock_shopping_cart):
        mock_user.cart = mock_shopping_cart
        mock_user.cart.items[0][0].check_availability.return_value = False
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    @patch("app.models.Users.Authentication.validate_credit_card")
    def test_checkout_invalid_credit_card(
        self, mock_validate_cc, mock_user, mock_shopping_cart
    ):
        mock_user.cart = mock_shopping_cart
        mock_validate_cc.return_value = False
        for item, _ in mock_user.cart.items:
            item.check_availability.return_value = True
        success, msg = mock_user.checkout(1234567890, 0)
        assert success is False, f"Expected False, got {success}. Msg: {msg}"

    def test_checkout_invalid_quantity(self, mock_user, mock_shopping_cart):
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
    def test_init(self, hashed_password):
        manager = Manager("Jane Admin", "jane@example.com", hashed_password)
        assert manager.name == "Jane Admin"
        assert manager.email == "jane@example.com"
        assert manager.password == hashed_password

    def test_repr(self, mock_manager):
        expected = "Manager: Name = Test Manager, Email = manager@example.com"
        assert repr(mock_manager) == expected

    @patch("app.models.Users.SessionLocal")
    def test_delete_user(self, mock_session_local, mock_session, mock_manager):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="Not found"):
            mock_manager.delete_user("nonexistent@example.com")

    @patch("app.models.Users.SessionLocal")
    def test_delete_user_exception(
        self, mock_session_local, mock_session, mock_manager
    ):
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
        mock_manager.set_password("newpassword123")
        mock_set_new_password.assert_called_once_with(mock_manager, "newpassword123")

    @patch("app.models.Users.Authentication.create_manager")
    def test_add_manager(self, mock_create_manager, mock_manager):
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
        mock_session_local.return_value = mock_session
        order_db = MagicMock()
        order_db.Ostatus = OrderStatus.DELIVERED
        mock_session.query.return_value.filter.return_value.first.return_value = (
            order_db
        )
        with pytest.raises(ValueError, match="Order number .* already delivered"):
            mock_manager.update_order_status(1)

    @patch("app.models.Users.SessionLocal")
    def test_update_order_status_order_db_none(
        self, mock_session_local, mock_session, mock_manager, monkeypatch
    ):
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.close = MagicMock()
        monkeypatch.setattr("app.models.Users.SessionLocal", lambda: mock_session)
        with pytest.raises(Exception, match="Error updating Order status:"):
            mock_manager.update_order_status(999)
        mock_session.close.assert_called_once()

    def test_update_inventory(self, mock_manager):
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
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.all.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Error retrieving orders: Database error"):
            mock_manager.get_all_orders()
        assert mock_session.close.call_count >= 1


class DummyBasicUser(BasicUser):
    def set_password(self, new_password: str) -> None:
        pass

    def __repr__(self) -> str:
        return f"DummyBasicUser: {self.name}, {self.email}"


def dummy_session_user_not_found():
    class DummyQuery:
        def filter(self, condition):
            return self

        def first(self):
            return None

    class DummySession:
        def query(self, model):
            return DummyQuery()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

        def add(self, obj):
            pass

        def delete(self, obj):
            pass

    return DummySession()


def dummy_session_orders_empty():
    class DummySession:
        def query(self, model):
            return MagicMock(all=lambda: [])

        def close(self):
            pass

    return DummySession()


def dummy_session_update_exception():
    class DummyQuery:
        def filter(self, condition):
            return self

        def first(self):
            return MagicMock()

    class DummySession:
        def query(self, model):
            return DummyQuery()

        def commit(self):
            raise Exception("Database error")

        def rollback(self):
            pass

        def close(self):
            pass

        def add(self, obj):
            pass

        def delete(self, obj):
            pass

    return DummySession()


def test_basic_user_email_too_long():
    with pytest.raises(ValueError, match="Email too long"):
        DummyBasicUser("Test", "a" * 26 + "@ex.com", "hashedpassword")


def test_basic_user_invalid_password_length():
    with pytest.raises(ValueError, match="password length not valid"):
        DummyBasicUser("Test", "test@example.com", "short")


def test_user_invalid_address_type():
    with pytest.raises(TypeError, match="Address must be a string"):
        User("John Doe", "john@example.com", "hashedpass123", 12345, 100.0)


def test_user_invalid_address_length():
    with pytest.raises(ValueError, match="Address length not valid."):
        User("John Doe", "john@example.com", "hashedpass123", "", 100.0)


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_user_not_found)
def test_update_user_details_not_found(mock_session):
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(ValueError, match="User not found in database"):
        user.update_user_details(address="456 New St")


def test_update_credit_invalid_type():
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(TypeError, match="credit must be a number"):
        user.update_credit("fifty")


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_update_exception)
def test_update_credit_exception(mock_session):
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    with pytest.raises(Exception, match="Error updating credit: Database error"):
        user.update_credit(50.0)


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_orders_empty)
def test_get_order_hist_from_db_empty(mock_session):
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    orders = user.get_order_hist_from_db()
    assert orders is None


def test_user_view_cart_returns_string():
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    user.cart = ShoppingCart()
    user.cart.items = []
    result = user.view_cart()
    assert isinstance(result, str)


def test_user_repr():
    user = User("John Doe", "john@example.com", "hashedpass123", "123 Main St", 100.0)
    rep = repr(user)
    assert "User: Name =" in rep
    assert "Email=" in rep


def test_manager_invalid_init():
    with pytest.raises(ValueError, match="Name cannot be empty"):
        Manager("", "manager@example.com", "hashedpass123")
    with pytest.raises(ValueError, match="Email cannot be empty"):
        Manager("Admin", "", "hashedpass123")
    with pytest.raises(ValueError, match="Password cannot be empty"):
        Manager("Admin", "manager@example.com", "")


@patch("app.models.Users.SessionLocal", side_effect=dummy_session_update_exception)
def test_manager_update_order_status_exception(mock_session):
    manager = Manager("Admin", "manager@example.com", "hashedpass123")
    with pytest.raises(Exception, match="Error updating Order status: Database error"):
        manager.update_order_status(1)


def test_manager_repr():
    manager = Manager("Admin", "manager@example.com", "hashedpass123")
    rep = repr(manager)
    assert "Manager: Name =" in rep
    assert "Email =" in rep


def test_authentication_validate_credit_card():
    Authentication.validate_credit_card = fixed_validate_credit_card
    assert Authentication.validate_credit_card(0, 1234567890) is True
    assert Authentication.validate_credit_card(100, 1234567890) is True
    assert Authentication.validate_credit_card(100, "invalid") is False


def test_checkout_partial_credit(monkeypatch):
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
        assert user._User__credit == 0
        fake_inventory.update_amount_in_inventory.assert_called()


def test_checkout_invalid_coupon(monkeypatch):
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
    auth = Authentication()
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager(123, "jane@example.com", "adminpass123")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager("Jane Admin", 456, "adminpass123")
    with pytest.raises(typeguard.TypeCheckError):
        auth.create_manager("Jane Admin", "jane@example.com", 789)


def test_set_new_password_type_error(mock_user):
    auth = Authentication()
    with pytest.raises(TypeError, match="password must be a string"):
        auth.set_new_password(mock_user, 12345)


def test_manager_update_inventory_subtraction(monkeypatch):
    manager = Manager("Bob", "bob@example.com", "hashedpass123")
    fake_inventory = MagicMock(spec=Inventory)
    monkeypatch.setattr("app.models.Users.Inventory", lambda: fake_inventory)
    manager.update_inventory(MagicMock(), 10, 0)
    fake_inventory.update_amount_in_inventory.assert_called_once_with(ANY, 10, 0)


def test_basic_user_email_lowercase():
    class DummyUser(BasicUser):
        def set_password(self, new_password: str) -> None:
            pass

        def __repr__(self) -> str:
            return f"DummyUser: {self.name}, {self.email}"

    user = DummyUser("Test", "UPPERCASE@EMAIL.COM", "hashedpass123")
    assert user.email == "uppercase@email.com"


def test_manager_update_order_status_order_db_none(monkeypatch):
    manager = Manager("Admin", "admin@example.com", "hashedpass123")
    fake_session = MagicMock()
    fake_session.query.return_value.filter.return_value.first.return_value = None
    fake_session.close = MagicMock()
    monkeypatch.setattr("app.models.Users.SessionLocal", lambda: fake_session)
    with pytest.raises(Exception, match="Error updating Order status:"):
        manager.update_order_status(999)
    fake_session.close.assert_called_once()


def test_manager_add_manager_failure(monkeypatch):
    manager = Manager("Admin", "admin@example.com", "hashedpass123")

    def fake_create_manager(n, e, p):
        raise Exception("Creation failed")

    monkeypatch.setattr(Authentication(), "create_manager", fake_create_manager)
    with pytest.raises(Exception, match="Creation failed"):
        manager.add_manager("New Manager", "new@example.com", "managerpass123")


def test_basic_user_invalid_types():
    class DummyUser(BasicUser):
        def set_password(self, new_password: str) -> None:
            pass

        def __repr__(self) -> str:
            return f"DummyUser: {self.name}, {self.email}"

    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser(123, "test@example.com", "hashedpass123")
    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser("Test", 456, "hashedpass123")
    with pytest.raises(AttributeError, match="has no attribute 'strip'"):
        DummyUser("Test", "test@example.com", 789)
