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
    """
    with app.test_client() as test_client:
        yield test_client


# -----------------------------------------------------------------------------------
# Basic /
# -----------------------------------------------------------------------------------
def test_home_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello, Welcome to our shop!" in response.data


# -----------------------------------------------------------------------------------
# update_inventory_by_manager Tests
# -----------------------------------------------------------------------------------


def test_update_inventory_by_manager_no_data(client):
    """
    If the route does not handle 'no data' gracefully, it might KeyError => 500.
    We send minimal JSON to ensure it returns 400 instead of KeyError => 500.
    """
    payload = {}
    response = client.put(
        "/update_inventory", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_update_inventory_by_manager_not_manager(client):
    """
    A regular user tries updating inventory. Expect 400 with
    'Only a logged-in administrator can update inventory'.
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
    mock_get_info.return_value = []
    response = client.get(
        "/get_furniture_info_by_price_range?min_price=100&max_price=200"
    )
    assert response.status_code == 200
    assert b"There are no furnitures in this price range" in response.data


def test_get_furniture_info_by_price_range_error(client):
    """
    If min_price or max_price aren't floats => 500
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
    A normal user tries to register a new manager.
    The code returns 400, not 500, because 'Only a logged-in administrator' can do it.
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
    mock_sign_in.return_value = None
    response = client.get("/sign_in?email=wrong@example.com&password=abc")
    assert response.status_code == 400
    assert b"Signing in failed" in response.data


# -----------------------------------------------------------------------------------
# view_shoppingcart Tests
# -----------------------------------------------------------------------------------
def test_view_shoppingcart_manager(client):
    manager_email = "manager2@example.com"
    cache_store[manager_email] = Manager(
        name="Mgr2", email=manager_email, password="abcdefgh"
    )

    response = client.get(f"/view_shoppingcart?email={manager_email}")
    assert response.status_code == 400
    assert b"You can see a shopping cart only as a user" in response.data


def test_view_shoppingcart_empty(client):
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


# -----------------------------------------------------------------------------------
# get_user's_orders_history Tests
# -----------------------------------------------------------------------------------
def test_get_users_orders_history_disconnected(client):
    user_email = "tempuser@example.com"
    cache_store[user_email] = None
    response = client.get(f"/get_user's_orders_history?email={user_email}")
    assert response.status_code == 400
    assert b"You have been disconnected from the site." in response.data


# -----------------------------------------------------------------------------------
# get_all_orders_by_manager Tests
# -----------------------------------------------------------------------------------
def test_get_all_orders_by_manager_not_manager(client):
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
    payload = {}
    response = client.put(
        "/add_item_to_cart", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_add_item_to_cart_not_user(client):
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
    payload = {}
    response = client.delete(
        "/remove_item_from_cart",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_remove_item_from_cart_not_user(client):
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
    payload = {}
    response = client.post(
        "/checkout", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


# -----------------------------------------------------------------------------------
# get_user_info Tests
# -----------------------------------------------------------------------------------
def test_get_user_info_not_found(client):
    response = client.get("/get_user_info?email=unknown@example.com")
    assert response.status_code == 400
    assert b"User or Manager must be logged in." in response.data


# -----------------------------------------------------------------------------------
# delete_user Tests
# -----------------------------------------------------------------------------------
def test_delete_user_no_email(client):
    payload = {}
    response = client.delete(
        "/delete_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No email provided" in response.data


def test_delete_user_not_manager(client):
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
    payload = {}
    response = client.put(
        "/update_password", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"Email and new password are required" in response.data


# -----------------------------------------------------------------------------------
# update_order_status Tests
# -----------------------------------------------------------------------------------
def test_update_order_status_no_data(client):
    payload = {}
    response = client.put(
        "/update_order_status",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert b"Email and order ID are required" in response.data


def test_update_order_status_not_manager(client):
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


# -----------------------------------------------------------------------------------
# apply_tax_on_user Tests
# -----------------------------------------------------------------------------------
def test_apply_tax_on_user_no_data(client):
    payload = {}
    response = client.put(
        "/apply_tax_on_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


def test_apply_tax_on_user_not_manager(client):
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


# -----------------------------------------------------------------------------------
# add_credit_to_user Tests
# -----------------------------------------------------------------------------------
def test_add_credit_to_user_no_data(client):
    payload = {}
    response = client.put(
        "/add_credit_to_user", data=json.dumps(payload), content_type="application/json"
    )
    assert response.status_code == 400
    assert b"No data provided" in response.data


@patch("app.models.Users.User.update_credit")
def test_add_credit_to_user_success(mock_update_credit, client):
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
    """Test retrieving furniture by price range with no results."""
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
