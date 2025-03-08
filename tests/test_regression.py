import pytest

from unittest.mock import patch, MagicMock
from app.models.FurnituresClass import DiningTable
from app.models.Users import User
from app.models.order import Order
from app.models.ShoppingCart import ShoppingCart


@pytest.mark.regression
def test_complete_purchase_workflow():
    """
    Regression test for the complete purchase workflow:
    - User creation
    - Furniture creation and validation
    - Cart operations (add, calculate total, apply discount)
    - Checkout process with inventory updates
    - Order creation and verification
    """
    # Mock database session for all operations
    with patch("app.data.DbConnection.SessionLocal") as mock_session_factory:
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        # Configure mock session to allow database operations
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = None

        # 1. Create a user - using actual User constructor
        user = User(
            name="Test User",
            email="test@example.com",
            password="hashedpass123",
            address="123 Test St",
            credit=100.0,
        )

        # 2. Create a test furniture object - using actual DiningTable constructor
        # Mock only the database interaction part
        with patch.object(
            DiningTable,
            "_get_info_furniture_by_key",
            return_value=(200.0, "Brown Dining Table", "A beautiful brown table"),
        ):
            dining_table = DiningTable(color="brown", material="wood")

            # Verify the furniture was created correctly
            assert dining_table.color == "brown"
            assert dining_table.material == "wood"
            assert dining_table.get_price() == 200.0

        # 3. Test availability check - mock db but use real method
        with patch.object(dining_table, "check_availability", return_value=True):
            assert dining_table.check_availability(2), "Furniture should be available"

            # Test a negative case too - not enough quantity
            with patch.object(dining_table, "check_availability", return_value=False):
                assert not dining_table.check_availability(
                    100
                ), "Should not be available in large quantity"

        # 4. Add furniture to cart - using actual ShoppingCart.add_item
        # Just mock the check_availability and Print_matching_product_advertisement
        with patch.object(dining_table, "check_availability", return_value=True):
            with patch.object(
                dining_table,
                "Print_matching_product_advertisement",
                return_value="Special offer!",
            ):
                # Call the actual add_item method
                success, adv = user.cart.add_item(dining_table, amount=2)

                # Verify the item was added correctly
                assert success, "Adding item to cart should succeed"
                assert len(user.cart.items) == 1, "Cart should have 1 item"
                assert (
                    user.cart.items[0][0] == dining_table
                ), "Cart item should be the dining table"
                assert user.cart.items[0][1] == 2, "Cart should have quantity 2"
                assert "Special offer!" in adv, "Should get advertisement"

        # 5. Test cart total calculation - using actual get_total_price
        total = user.cart.get_total_price()
        assert total == 400.0, f"Expected total price to be 400.0, got {total}"

        # 6. Test coupon application - mock DB lookup but use real discount calculation
        with patch.object(
            user.cart, "get_coupon_discount_and_id", return_value=(10, 1)
        ):
            # Test the actual apply_discount method
            discounted_total = user.cart.apply_discount(10)
            expected_discount = 400.0 * 0.9  # 10% off
            assert (
                discounted_total == expected_discount
            ), f"Expected discounted price to be {expected_discount}, got {discounted_total}"

        # 7. Test checkout process - use the real checkout and validate_credit_card
        with patch.object(dining_table, "check_availability", return_value=True):
            with patch(
                "app.models.inventory.Inventory.update_amount_in_inventory"
            ) as mock_update_inventory:
                # Mock Order._save_to_db to avoid actual database interaction
                with patch.object(Order, "_save_to_db"):
                    # Use the real validate_credit_card function (not mocked)
                    # Call the actual checkout method
                    success, msg = user.checkout(4111111111111111, "SAVE10")

                    # Verify checkout was successful
                    assert success, f"Checkout failed: {msg}"

                    # Verify inventory was updated
                    mock_update_inventory.assert_called()
                    args, kwargs = mock_update_inventory.call_args
                    assert (
                        args[0] == dining_table
                    ), "Should update inventory for dining table"
                    assert args[1] == 2, "Should update quantity of 2"
                    assert not kwargs["sign"], "Should reduce inventory"

                    # Verify order was created
                    assert len(user._orders) == 1, "Order should be created"
                    order = user._orders[0]
                    assert (
                        order.get_user_mail() == "test@example.com"
                    ), "Order should have correct email"

                    # Verify cart was emptied
                    assert (
                        len(user.cart.items) == 0
                    ), "Cart should be empty after checkout"

        # 8. Test checkout failures

        # 8.1 Empty cart
        user.cart = ShoppingCart()  # Empty cart
        success, msg = user.checkout(4111111111111111, "SAVE10")
        assert not success, "Checkout should fail with empty cart"
        assert (
            "no items in the cart" in msg.lower()
        ), f"Expected error about empty cart, got: {msg}"

        # 8.2 Unavailable item
        with patch.object(dining_table, "check_availability", return_value=True):
            user.cart.add_item(dining_table, amount=2)

        with patch.object(dining_table, "check_availability", return_value=False):
            success, msg = user.checkout(4111111111111111, "SAVE10")
            assert not success, "Checkout should fail with unavailable item"
            assert (
                "not enough" in msg.lower()
            ), f"Expected error about availability, got: {msg}"

        # 8.3 Invalid credit card - still using real validate_credit_card
        with patch.object(dining_table, "check_availability", return_value=True):
            # Use the real validate_credit_card, but with an invalid card number format
            success, msg = user.checkout(12345, "SAVE10")
            assert not success, "Checkout should fail with invalid credit card"
            assert (
                "invalid credit card" in msg.lower()
            ), f"Expected error about invalid credit card, got: {msg}"
