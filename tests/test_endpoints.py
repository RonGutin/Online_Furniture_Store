import pytest
import json
from unittest.mock import patch, MagicMock

# Ensure you import from your actual endpoints module:
from app.api.endpoints import app, cache_store
from app.models.Users import User, Manager


@pytest.fixture
def client():
    """
    Pytest fixture to create a test client for our Flask app.

    Returns:
        Flask test client: A test client for the Flask application.
    """
    with app.test_client() as test_client:
        yield test_client


# -----------------------------------------------------------------------------------
# Basic /
# -----------------------------------------------------------------------------------
def test_home_route(client):
    """
    Test that the home route responds with a 200 status code and expected welcome message.

    Args:
        client: The Flask test client fixture.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello, Welcome to our shop!" in response.data


# -----------------------------------------------------------------------------------
# update_inventory_by_manager Tests
# -----------------------------------------------------------------------------------


def test_update_inventory_by_manager_no_data(client):
    """
    Test updating inventory when no data is provided.

    Tests if the route handles 'no data' gracefully instead of returning a 500 error.
    Expects a 400 status code with a specific error message.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/update_inventory", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_update_inventory_by_manager_not_manager(client):
    """
    Test updating inventory when a regular user attempts to update inventory.

    Expects a 400 status code with a message indicating only administrators can update inventory.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "user@example.com"
    cache_store[user_email] = User(
        name="UserName", email=user_email, password="12345678", address="User address"
    )

    payload = {
        "quantity": 10,
        "sign": "-",
        "object_type": "table",
        "item": {"color": "brown", "table": {"material": "wood"}},
        "existing_admin_email": user_email,
    }
    response = client.put(
        "/update_inventory", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"Only a logged-in administrator can update inventory" in response.data


# -----------------------------------------------------------------------------------
# get_furniture_info_by_price_range Tests
# -----------------------------------------------------------------------------------
@patch("app.models.inventory.Inventory.get_information_by_price_range")
def test_get_furniture_info_by_price_range_success(mock_get_info, client):
    """
    Test successful retrieval of furniture information by price range.

    Args:
        mock_get_info: Mock for the get_information_by_price_range method.
        client: The Flask test client fixture.
    """
    mock_get_info.return_value = [
        {"name": "Test Chair", "price": 150.0},
        {"name": "Test Table", "price": 120.0},
    ]
    response = client.get(
        "/get_furniture_info_by_price_range?min_price=100&max_price=200"
    )
    assert response.status_code == 200
    assert b"Test Chair" in response.data
    assert b"Test Table" in response.data


@patch("app.models.inventory.Inventory.get_information_by_price_range")
def test_get_furniture_info_by_price_range_none_found(mock_get_info, client):
    """
    Test retrieving furniture by price range when no items are found.

    Args:
        mock_get_info: Mock for the get_information_by_price_range method.
        client: The Flask test client fixture.
    """
    mock_get_info.return_value = []
    response = client.get(
        "/get_furniture_info_by_price_range?min_price=100&max_price=200"
    )
    assert response.status_code == 200
    assert b"There are no furnitures in this price range" in response.data


def test_get_furniture_info_by_price_range_error(client):
    """
    Test error handling when invalid price values are provided.

    Tests if the endpoint handles non-float values for min_price and max_price by returning 500.

    Args:
        client: The Flask test client fixture.
    """
    response = client.get(
        "/get_furniture_info_by_price_range?min_price=abc&max_price=def"
    )
    assert response.status_code == 500


# -----------------------------------------------------------------------------------
# user_register Tests
# -----------------------------------------------------------------------------------
@patch("app.models.Users.Authentication.create_user")
def test_user_register_success(mock_create_user, client):
    """
    Test successful user registration.

    Args:
        mock_create_user: Mock for the create_user method.
        client: The Flask test client fixture.
    """
    user_obj = User(
        name="TestUser",
        email="testuser@example.com",
        password="12345678",
        address="some address",
    )
    mock_create_user.return_value = user_obj

    payload = {
        "name": "TestUser",
        "email": "testuser@example.com",
        "password": "12345678",
        "address": "some address",
        "credit": 100,
    }
    response = client.post(
        "/user_register", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    assert b"User TestUser created successfully" in response.data
    assert "testuser@example.com" in cache_store


@patch("app.models.Users.Authentication.create_user")
def test_user_register_failure(mock_create_user, client):
    """
    Test user registration when creation fails.

    Args:
        mock_create_user: Mock for the create_user method.
        client: The Flask test client fixture.
    """
    mock_create_user.return_value = None

    payload = {
        "name": "FailUser",
        "email": "failuser@example.com",
        "password": "12345678",
        "address": "Somewhere",
    }
    response = client.post(
        "/user_register", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"User creation failed" in response.data


def test_secondary_manager_register_no_manager(client):
    """
    Test manager registration by a non-manager user.

    Tests that a normal user cannot register a new manager and receives a 400 status code.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "normaluser@example.com"
    cache_store[user_email] = User(
        name="SomeUser", email=user_email, password="12345678", address="Some Address"
    )
    payload = {
        "existing_admin_email": user_email,
        "name": "NewManager",
        "email": "new_manager@example.com",
        "password": "password8",
    }
    response = client.post(
        "/secondary_manager_register",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"Only a logged-in administrator can create" in response.data


@patch("app.api.endpoints.MAIN_MANAGER.add_manager")
def test_secondary_manager_register_success(mock_add_manager, client):
    """
    Test successful secondary manager registration by an existing manager.

    Args:
        mock_add_manager: Mock for the add_manager method.
        client: The Flask test client fixture.
    """
    mock_new_mgr = Manager(
        name="NewManager", email="new_manager@example.com", password="password8"
    )
    mock_add_manager.return_value = mock_new_mgr

    existing_mgr_email = "existing_mgr@example.com"
    cache_store[existing_mgr_email] = Manager(
        name="BossUser", email=existing_mgr_email, password="bosspassword"
    )
    payload = {
        "existing_admin_email": existing_mgr_email,
        "name": "NewManager",
        "email": "new_manager@example.com",
        "password": "password8",
    }
    response = client.post(
        "/secondary_manager_register",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert b"Manager NewManager created successfully" in response.data
    assert "new_manager@example.com" in cache_store


# -----------------------------------------------------------------------------------
# sign_in Tests
# -----------------------------------------------------------------------------------
@patch("app.models.Users.Authentication.sign_in")
def test_sign_in_success(mock_sign_in, client):
    """
    Test successful user sign-in.

    Args:
        mock_sign_in: Mock for the sign_in method.
        client: The Flask test client fixture.
    """
    mock_user = User(
        name="MockUser",
        email="mockuser@example.com",
        password="12345678",
        address="somewhere",
    )
    mock_sign_in.return_value = mock_user

    response = client.get("/sign_in?email=mockuser@example.com&password=12345678")
    assert response.status_code == 200
    assert b"Signing in was successful" in response.data
    assert "mockuser@example.com" in cache_store


@patch("app.models.Users.Authentication.sign_in")
def test_sign_in_failure(mock_sign_in, client):
    """
    Test sign-in failure with invalid credentials.

    Args:
        mock_sign_in: Mock for the sign_in method.
        client: The Flask test client fixture.
    """
    mock_sign_in.return_value = None
    response = client.get("/sign_in?email=wrong@example.com&password=abc")
    assert response.status_code == 400
    assert b"Signing in failed" in response.data


def test_sign_in_error(client):
    """
    Test error handling in the sign_in endpoint when required parameters are missing.

    Args:
        client: The Flask test client fixture.
    """
    # Cause an exception by not providing required parameters
    response = client.get("/sign_in")  # Missing email and password
    assert response.status_code == 500
    response_data = json.loads(response.data)
    assert "Error while signing in" in response_data["message"]


# -----------------------------------------------------------------------------------
# view_shoppingcart Tests
# -----------------------------------------------------------------------------------
def test_view_shoppingcart_manager(client):
    """
    Test that a manager cannot view a shopping cart.

    Args:
        client: The Flask test client fixture.
    """
    manager_email = "manager2@example.com"
    cache_store[manager_email] = Manager(
        name="Mgr2", email=manager_email, password="abcdefgh"
    )

    response = client.get(f"/view_shoppingcart?email={manager_email}")
    assert response.status_code == 400
    assert b"You can see a shopping cart only as a user" in response.data


def test_view_shoppingcart_empty(client):
    """
    Test viewing an empty shopping cart.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "userx@example.com"
    user = User(
        name="UserX", email=user_email, password="12345678", address="UserX address"
    )
    user.cart.view_cart = MagicMock(return_value=[])
    cache_store[user_email] = user

    response = client.get(f"/view_shoppingcart?email={user_email}")
    assert response.status_code == 200
    assert b"your shopping cart is empty" in response.data


# -----------------------------------------------------------------------------------
# edit_user's_details Tests
# -----------------------------------------------------------------------------------
def test_edit_users_details_no_updates(client):
    """
    Test editing user details with no updates provided.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "someuser@example.com"
    cache_store[user_email] = User(
        name="SomeUser", email=user_email, password="12345678", address="Some address"
    )
    payload = {"email": user_email}
    response = client.put(
        "/edit_user's_details",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"No details were submitted for update." in response.data


def test_edit_users_details_success(client):
    """
    Test successful user details update with new name and address.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "test_user@example.com"
    test_user = User(
        name="Edit Test User",
        email=user_email,
        password="12345678",
        address="Original Address",
    )
    # Mock update_user_details to avoid DB calls
    test_user.update_user_details = MagicMock()
    cache_store[user_email] = test_user

    payload = {
        "email": user_email,
        "new_address": "New Address",
        "new_name": "New Name",
    }
    response = client.put(
        "/edit_user's_details",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "successfully updated" in response_data["message"]
    test_user.update_user_details.assert_called_once_with(
        address="New Address", name="New Name"
    )


# -----------------------------------------------------------------------------------
# get_user's_orders_history Tests
# -----------------------------------------------------------------------------------
def test_get_users_orders_history_disconnected(client):
    """
    Test retrieving order history for a disconnected user.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "tempuser@example.com"
    cache_store[user_email] = None
    response = client.get(f"/get_user's_orders_history?email={user_email}")
    assert response.status_code == 400
    assert b"You have been disconnected from the site." in response.data


# -----------------------------------------------------------------------------------
# get_all_orders_by_manager Tests
# -----------------------------------------------------------------------------------
def test_get_all_orders_by_manager_not_manager(client):
    """
    Test that a non-manager user cannot get all orders.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "normal_user@example.com"
    cache_store[user_email] = User(
        name="NormalUser",
        email=user_email,
        password="12345678",
        address="Normal address",
    )
    response = client.get(f"/get_all_orders_by_manager?email={user_email}")
    assert response.status_code == 400
    assert b"Only a manager can see all order's history." in response.data


# -----------------------------------------------------------------------------------
# add_item_to_cart Tests
# -----------------------------------------------------------------------------------
def test_add_item_to_cart_no_data(client):
    """
    Test adding an item to cart with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/add_item_to_cart", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_add_item_to_cart_not_user(client):
    """
    Test that a manager cannot add items to a cart.

    Args:
        client: The Flask test client fixture.
    """
    manager_email = "manager4@example.com"
    cache_store[manager_email] = Manager(
        name="Manager4", email=manager_email, password="mypassword"
    )
    payload = {
        "email": manager_email,
        "object_type": "chair",
        "item": {
            "color": "blue",
            "chair": {"is_adjustable": True, "has_armrest": True},
        },
    }
    response = client.put(
        "/add_item_to_cart", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"Only a user can add furniture to shopping cart." in response.data


# -----------------------------------------------------------------------------------
# remove_item_from_cart Tests
# -----------------------------------------------------------------------------------
def test_remove_item_from_cart_no_data(client):
    """
    Test removing an item from cart with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.delete(
        "/remove_item_from_cart",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_remove_item_from_cart_not_user(client):
    """
    Test that a manager cannot remove items from a cart.

    Args:
        client: The Flask test client fixture.
    """
    manager_email = "manager5@example.com"
    cache_store[manager_email] = Manager(
        name="Manager5", email=manager_email, password="12345678"
    )
    payload = {
        "email": manager_email,
        "object_type": "table",
        "item": {"color": "white", "table": {"material": "wood"}},
    }
    response = client.delete(
        "/remove_item_from_cart",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"Only a user can remove furniture" in response.data


# -----------------------------------------------------------------------------------
# checkout_endpoint Tests
# -----------------------------------------------------------------------------------
def test_checkout_no_data(client):
    """
    Test checkout with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.post(
        "/checkout", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_checkout_success(client):
    """
    Test successful checkout process with credit card and coupon code.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "checkout@example.com"
    test_user = User(
        name="Checkout User",
        email=user_email,
        password="12345678",
        address="Checkout Address",
    )
    test_user.checkout = MagicMock(return_value=(True, "Checkout successful!"))
    cache_store[user_email] = test_user

    payload = {
        "email": user_email,
        "credit_card_num": 4111111111111111,
        "coupon_code": "SAVE10",
    }
    response = client.post(
        "/checkout", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data["message"] == "Checkout successful!"
    test_user.checkout.assert_called_once_with(4111111111111111, "SAVE10")


# -----------------------------------------------------------------------------------
# get_user_info Tests
# -----------------------------------------------------------------------------------
def test_get_user_info_not_found(client):
    """
    Test getting user info for a non-existent user.

    Args:
        client: The Flask test client fixture.
    """
    response = client.get("/get_user_info?email=unknown@example.com")
    assert response.status_code == 400
    assert b"User or Manager must be logged in." in response.data


# -----------------------------------------------------------------------------------
# delete_user Tests
# -----------------------------------------------------------------------------------
def test_delete_user_no_email(client):
    """
    Test deleting a user without providing an email.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.delete(
        "/delete_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No email provided" in response.data


def test_delete_user_not_manager(client):
    """
    Test that a non-manager user cannot delete users.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "test_user@example.com"
    cache_store[user_email] = User(
        name="TestUser", email=user_email, password="12345678", address="Test address"
    )
    payload = {"email": user_email, "email_to_delete": "someone_else@example.com"}
    response = client.delete(
        "/delete_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"Only a manager can delete users." in response.data


# -----------------------------------------------------------------------------------
# update_password Tests
# -----------------------------------------------------------------------------------
def test_update_password_no_data(client):
    """
    Test updating password with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/update_password", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"Email and new password are required" in response.data


def test_update_password_success(client):
    """
    Test successful password update.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "password@example.com"
    test_user = User(
        name="Password User",
        email=user_email,
        password="12345678",
        address="Password Address",
    )
    test_user.set_password = MagicMock()
    cache_store[user_email] = test_user

    payload = {"email": user_email, "new_password": "newpassword123"}
    response = client.put(
        "/update_password", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "Password updated successfully" in response_data["message"]
    test_user.set_password.assert_called_once_with("newpassword123")


# -----------------------------------------------------------------------------------
# update_order_status Tests
# -----------------------------------------------------------------------------------
def test_update_order_status_no_data(client):
    """
    Test updating order status with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/update_order_status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"Email and order ID are required" in response.data


def test_update_order_status_not_manager(client):
    """
    Test that a non-manager user cannot update order status.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "just_a_user@example.com"
    cache_store[user_email] = User(
        name="JustAUser", email=user_email, password="12345678", address="User address"
    )
    payload = {"email": user_email, "order_id": "12345"}
    response = client.put(
        "/update_order_status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert b"Only a manager can update order status." in response.data


def test_update_order_status_success(client):
    """
    Test successful order status update by a manager.

    Args:
        client: The Flask test client fixture.
    """
    manager_email = "order_manager@example.com"
    test_manager = Manager(
        name="Order Manager", email=manager_email, password="12345678"
    )
    test_manager.update_order_status = MagicMock()
    cache_store[manager_email] = test_manager

    payload = {"email": manager_email, "order_id": 123}
    response = client.put(
        "/update_order_status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "status updated successfully" in response_data["message"]
    test_manager.update_order_status.assert_called_once_with(123)


# -----------------------------------------------------------------------------------
# apply_tax_on_user Tests
# -----------------------------------------------------------------------------------
def test_apply_tax_on_user_no_data(client):
    """
    Test applying tax on user with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/apply_tax_on_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_apply_tax_on_user_not_manager(client):
    """
    Test that a non-manager user cannot apply tax to a user's cart.

    Args:
        client: The Flask test client fixture.
    """
    user_email = "norm_user@example.com"
    cache_store[user_email] = User(
        name="NormUser", email=user_email, password="12345678", address="norm address"
    )
    payload = {
        "manager_email": user_email,
        "user_email": "another_user@example.com",
        "tax_rate": 15,
    }
    response = client.put(
        "/apply_tax_on_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 403
    assert b"Only a manager can apply tax to a user's cart." in response.data


def test_apply_tax_on_user_success(client):
    """
    Test successful tax application by a manager to a user's cart.

    Args:
        client: The Flask test client fixture.
    """
    manager_email = "tax_manager@example.com"
    test_manager = Manager(name="Tax Manager", email=manager_email, password="12345678")
    cache_store[manager_email] = test_manager

    user_email = "tax_user@example.com"
    test_user = User(
        name="Tax User", email=user_email, password="12345678", address="Tax Address"
    )
    test_user.cart.apply_tax_on_cart = MagicMock(return_value=True)
    cache_store[user_email] = test_user

    payload = {"manager_email": manager_email, "user_email": user_email, "tax_rate": 10}
    response = client.put(
        "/apply_tax_on_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "applied successfully" in response_data["message"]
    test_user.cart.apply_tax_on_cart.assert_called_once_with(10)


# -----------------------------------------------------------------------------------
# add_credit_to_user Tests
# -----------------------------------------------------------------------------------
def test_add_credit_to_user_no_data(client):
    """
    Test adding credit to user with no data provided.

    Args:
        client: The Flask test client fixture.
    """
    payload = {}
    response = client.put(
        "/add_credit_to_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


@patch("app.models.Users.User.update_credit")
def test_add_credit_to_user_success(mock_update_credit, client):
    """
    Test successful credit addition to a user by a manager.

    Args:
        mock_update_credit: Mock for the update_credit method.
        client: The Flask test client fixture.
    """
    manager_email = "mgr11@example.com"
    cache_store[manager_email] = Manager(
        name="Mgr11", email=manager_email, password="longpassword"
    )
    user_email = "user11@example.com"
    cache_store[user_email] = User(
        name="User11", email=user_email, password="12345678", address="User11 address"
    )

    payload = {"manager_email": manager_email, "user_email": user_email, "credit": 100}
    response = client.put(
        "/add_credit_to_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 200
    assert b"Successfully updated user11@example.com's credit by 100" in response.data
    mock_update_credit.assert_called_once_with(100)


def test_get_furniture_info_by_price_range_no_results(client):
    """
    Test retrieving furniture by price range when no items are found in the mocked inventory.

    Args:
        client: The Flask test client fixture.
    """
    with patch("app.api.endpoints.Inventory") as mock_inventory:
        mock_inv_instance = MagicMock()
        mock_inventory.return_value = mock_inv_instance
        mock_inv_instance.get_information_by_price_range.return_value = []

        response = client.get(
            "/get_furniture_info_by_price_range?min_price=1000&max_price=2000"
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "no furnitures in this price range" in response_data["message"]


def test_update_inventory_by_manager_not_logged_in(client):
    """Test updating inventory when manager is not logged in."""
    data = {
        "quantity": 10,
        "sign": True,
        "object_type": "DINING_TABLE",
        "item": {"color": "brown", "table": {"material": "wood"}},
        "existing_admin_email": "nonexistent@example.com",
    }
    response = client.put("/update_inventory", json=data)
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "administrator" in response_data["message"]


def test_view_shoppingcart_not_logged_in(client):
    """Test view shopping cart when user is not logged in."""
    response = client.get("/view_shoppingcart?email=nonexistent@example.com")
    assert response.status_code == 400
    response_data = json.loads(response.data)
    assert "must be logged in" in response_data["message"]
