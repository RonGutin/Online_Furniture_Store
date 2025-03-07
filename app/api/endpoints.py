from flask import jsonify, request, Flask
from app.models.inventory import Inventory
from app.models.FurnitureFactory import FurnitureFactory
from app.models.Users import Authentication, Manager, User
from cachetools import TTLCache

app = Flask(__name__)


@app.after_request
def add_cache_headers(response):
    if request.method == "GET":
        response.headers["Cache-Control"] = "public, max-age=3600"
    else:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def home():
    return "Hello, Welcome to our shop!"


MAIN_MANAGER = Manager(
    email="hili@example.com", name="Hili", password="password4"
)  # DO NOT DELETE OR CHANGE THIS VARIABLE!!!!
cache_store = TTLCache(maxsize=100, ttl=3600)


@app.route("/update_inventory", methods=["PUT"])
def update_inventory_by_manager():
    """
    Handle inventory updates for a logged-in manager.

    This function processes a PUT request to update the inventory of furniture items.
    It requires a valid, logged-in manager (identified by 'existing_admin_email' in the
    JSON payload) and uses the FurnitureFactory to create furniture items according to
    the specified parameters ('table' or 'chair' attributes). The inventory is then
    updated through the MAIN_MANAGER instance.

    Returns:
        flask.Response: A JSON response with a success message and HTTP status 200 if the
        update is successful, or an error message with the appropriate HTTP status code
        if any step fails.

    Raises:
        500 Internal Server Error: If any unexpected exception occurs during the process.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        quantity = data.get("quantity")
        sign = data.get("sign")
        object_type = data.get("object_type")
        item = data.get("item")
        color = item["color"]
        existing_admin_email = data["existing_admin_email"]
        if existing_admin_email not in cache_store:
            return (
                jsonify(
                    {
                        "message": (
                            "Only a logged-in administrator can update inventory,"
                            "Please log in."
                        )
                    }
                ),
                400,
            )
        user_inst = cache_store.get(existing_admin_email)
        if not isinstance(user_inst, Manager):
            return (
                jsonify(
                    {"message": "Only a logged-in administrator can update inventory."}
                ),
                400,
            )

        furniture_factory = FurnitureFactory()

        if "table" in item:
            material = item["table"]["material"]
            item_object = furniture_factory.create_furniture(
                furniture_type=object_type, color=color, material=material
            )

        if "chair" in item:
            is_adjustable = item["chair"]["is_adjustable"]
            has_armrest = item["chair"]["has_armrest"]
            item_object = furniture_factory.create_furniture(
                furniture_type=object_type,
                color=color,
                is_adjustable=is_adjustable,
                has_armrest=has_armrest,
            )

        if not item_object:
            return (
                jsonify(
                    {
                        "message": "There is no furniture that "
                        "has the characteristics you specified."
                    }
                ),
                404,
            )

        MAIN_MANAGER.update_inventory(item=item_object, quantity=quantity, sign=sign)
        return jsonify({"message": "Inventory updated successfully."}), 200

    except Exception as es:
        return jsonify({"message": f"Error updating Inventory: {es}"}), 500


@app.route("/get_furniture_info_by_price_range", methods=["GET"])
def get_furniture_info_by_price_range():
    """
    Retrieve furniture information within a specified price range.

    This endpoint expects two query parameters, 'min_price' and 'max_price',
    which are used to filter the furniture items stored in the Inventory.
    The function returns a list of furniture items if any are found within
    the specified price range, or a message indicating that no items match
    the range.

    Query Parameters:
        min_price (float): The minimum price in the range.
        max_price (float): The maximum price in the range.

    Returns:
        flask.Response: A JSON response with:
            - A list of furniture items (HTTP 200) if items are found.
            - A message indicating no furniture items in that range (HTTP 200).
            - A message indicating an error (HTTP 500) if something goes wrong.
    """

    try:
        max_price = float(request.args.get("max_price"))
        min_price = float(request.args.get("min_price"))
        inv = Inventory()
        res = inv.get_information_by_price_range(
            min_price=min_price, max_price=max_price
        )
        if res is None:
            return jsonify({"message": "Error while processing request"}), 500
        elif len(res) > 0:
            return res, 200
        return jsonify({"message": "There are no furnitures in this price range"}), 200
    except Exception as es:
        return jsonify({"message": f"Error while processing request: {es}"}), 500


@app.route("/user_register", methods=["POST"])
def user_register():
    """
    Register a new user in the system.

    This endpoint expects a JSON payload with the following keys:
    - name (str): The user's full name.
    - email (str): The user's email address.
    - password (str): The user's chosen password.
    - address (str): The user's address.
    - credit (int, optional): The user's initial credit balance.

    The function creates a new user using the Authentication class, stores the
    user in the cache_store, and returns a JSON response indicating success or
    failure.

    Returns:
        flask.Response: A JSON response with a success message if the user is
        created successfully (HTTP 200), or an error message if the user
        creation fails (HTTP 400), or a server error message (HTTP 500) if an
        exception occurs.
    """
    try:
        auth = Authentication()
        data = request.get_json()
        name = data["name"]
        email = data["email"]
        password = data["password"]
        address = data["address"]
        credit = 0
        if "credit" in data:
            credit = data["credit"]
        res = auth.create_user(
            name=name, email=email, password=password, address=address, credit=credit
        )
        cache_store[email] = res
        if isinstance(res, User):
            return (
                jsonify(
                    {
                        "message": f"User {res.name} created successfully,"
                        f"the usename for connection is: {res.email}"
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": "User creation failed,"
                        "probably because user details are already in use or"
                        "the details were transferred incorrectly"
                    }
                ),
                400,
            )
    except Exception as es:
        return jsonify({"message": f"Error while registertion: {es}"}), 500


@app.route("/secondary_manager_register", methods=["POST"])
def manager_register():
    """
    Register a new secondary manager in the system.

    This endpoint requires a valid existing_admin_email for authentication,
    ensuring that only a logged-in administrator (Manager) can register new
    managers. If validation succeeds, the function creates a new Manager
    with the provided name, email, and password, then stores it in cache_store.

    JSON Payload:
        existing_admin_email (str): Email of the currently logged-in administrator.
        name (str): The name of the new manager.
        email (str): The email address of the new manager.
        password (str): The password for the new manager.

    Returns:
        flask.Response: A JSON response with one of the following outcomes:
            - Success message (HTTP 200) if the manager is created successfully.
            - Error message (HTTP 400) if creation fails or if the user is not
              authorized to register a new manager.
            - Server error message (HTTP 500) if an unexpected exception occurs.
    """
    try:
        data = request.get_json()
        existing_admin_email = data["existing_admin_email"]
        name = data["name"]
        email = data["email"]
        password = data["password"]
        if existing_admin_email not in cache_store:
            return (
                jsonify(
                    {
                        "message": (
                            "Only a logged-in administrator can create"
                            "a new administrator account."
                        )
                    }
                ),
                400,
            )
        user_inst = cache_store.get(existing_admin_email)
        if not isinstance(user_inst, Manager):
            return (
                jsonify(
                    {
                        "message": (
                            "Only a logged-in administrator can create"
                            "a new administrator account."
                        )
                    }
                ),
                400,
            )

        res = MAIN_MANAGER.add_manager(name=name, email=email, password=password)
        cache_store[email] = res
        if isinstance(res, Manager):
            return (
                jsonify(
                    {
                        "message": f"Manager {res.name} created successfully,"
                        f"the usename for connection is: {res.email}"
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": "Manager creation failed,"
                        "probably because user details are already in use"
                        "or the details were transferred incorrectly"
                    }
                ),
                400,
            )
    except Exception as es:
        return jsonify({"message": f"Error while registertion manager: {es}"}), 500


@app.route("/sign_in", methods=["GET"])
def user_sign_in():
    try:
        email = request.args.get("email")
        password = request.args.get("password")
        auth = Authentication()
        res = auth.sign_in(email=email, password=password)
        if isinstance(res, (Manager, User)):
            user_data = res.to_dict_without_password()
            cache_store[email] = res
            return (
                jsonify(
                    {
                        "user_data": user_data,
                        "message": f"Signing in was successful!"
                        f"You are logged in to our site, {res.name} - welcome back!",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "message": "Signing in failed, check the details you entered and try again"
                    }
                ),
                400,
            )
    except Exception as es:
        return jsonify({"message": f"Error while signing in: {es}"}), 500


@app.route("/view_shoppingcart", methods=["GET"])
def view_shoppingcart():
    """
    Display the contents of a user's shopping cart.

    This endpoint requires a query parameter 'email', which corresponds to a logged-in
    user in the cache_store. If the user is not found, or if the user is a manager, an
    error message is returned. Otherwise, the function retrieves and displays the items
    in the user's cart. If the cart is empty, a corresponding message is provided.

    Query Parameters:
        email (str): The email of the logged-in user.

    Returns:
        flask.Response: A JSON response indicating either:
            - The cart contents (HTTP 200) if the user exists and is not a manager.
            - An error message (HTTP 400) if the user is not logged in or is a manager.
            - A server error message (HTTP 500) if any exception occurs while processing
              the request.
    """
    try:
        email = request.args.get("email")
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to view your shopping cart."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if isinstance(user_inst, Manager):
            return (
                jsonify(
                    {
                        "message": "You can see a shopping cart only as a user."
                        "you logged in as a manager."
                    }
                ),
                400,
            )
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to view your shopping cart."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        try:
            res = user_inst.cart.view_cart()
            if not res:
                return jsonify({"message": "your shopping cart is empty"}), 200
            return jsonify({"your shopping cart": res}), 200
        except Exception as es:
            return jsonify({"message": f"Error showing cart: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Error while signing in: {es}"}), 500


@app.route("/edit_user's_details", methods=["PUT"])
def edit_users_details():
    """
    Edit the details of a logged-in user or manager.

    This endpoint expects a JSON payload containing:
    - email (str): The user's or manager's email (must be logged in).
    - new_address (str, optional): The updated address.
    - new_name (str, optional): The updated name.

    If the user corresponding to the given email is not logged in or doesn't exist
    in cache_store, an error message is returned. Otherwise, the provided new
    details (address, name, or both) are updated for the user or manager.

    Returns:
        flask.Response:
            - A success message (HTTP 200) if details are successfully updated.
            - An error message (HTTP 400) if the user is not logged in, disconnected,
              or if no new details are provided for update.
            - A server error message (HTTP 500) if any exception occurs while editing
              the details.
    """
    try:
        data = request.get_json()
        email = data.get("email")
        new_address = data.get("new_address", None)
        new_name = data.get("new_name", None)
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to edit your details."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You have been disconnected from the site."
                        "Please reconnect and try again."
                    }
                ),
                400,
            )
        if isinstance(user_inst, (Manager, User)):
            if not new_name and not new_address:
                return (
                    jsonify({"message": "No details were submitted for update."}),
                    400,
                )
            try:
                user_inst.update_user_details(address=new_address, name=new_name)
                return (
                    jsonify(
                        {"message": "Your details have been successfully updated."}
                    ),
                    200,
                )
            except Exception as es:
                return jsonify({"message": f"Error while editing details: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Connection error: {es}"}), 500


@app.route("/get_user's_orders_history", methods=["GET"])
def get_users_orders_history():
    """
    Retrieve the order history of a logged-in user.

    This endpoint expects a query parameter 'email' that identifies the user
    in the cache_store. If the user does not exist or is disconnected from
    the site, an error message is returned. If the user has no orders, a
    corresponding message is returned. Otherwise, the function provides the
    user's complete order history.

    Query Parameter:
        email (str): The email of the logged-in user.

    Returns:
        flask.Response:
            - A JSON response containing the user's order history (HTTP 200).
            - An error message (HTTP 400) if the user is not found or has been
              disconnected.
            - A server error message (HTTP 500) if an exception occurs.
    """
    try:
        email = request.args.get("email")
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to edit your details."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You have been disconnected from the site."
                        "Please reconnect and try again."
                    }
                ),
                400,
            )
        try:
            res = user_inst.get_order_hist_from_db()
            if not res:
                return jsonify({"message": "You have no orders at all"}), 200
            return jsonify({"your orders history": res}), 200
        except Exception as es:
            return jsonify({"message": f"Error showing orders history: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Connection error: {es}"}), 500


@app.route("/get_all_orders_by_manager", methods=["GET"])
def get_all_orders_by_manager():
    """
    Retrieve all orders in the system, accessible only to managers.

    This endpoint requires a query parameter 'email' associated with a
    manager account. If the email is not found in cache_store or the user is
    not a manager, an error message is returned. Otherwise, it fetches all
    orders in the order history.

    Query Parameter:
        email (str): The email of a logged-in manager.

    Returns:
        flask.Response:
            - A JSON response with all orders in the system (HTTP 200) if
              the email belongs to a manager and there are orders.
            - A message indicating no orders exist (HTTP 200) if none are found.
            - An error message (HTTP 400) if the user is not a manager or is
              disconnected.
            - A server error message (HTTP 500) if an exception occurs.
    """
    try:
        email = request.args.get("email")
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to see all orders."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You have been disconnected from the site."
                        "Please reconnect and try again."
                    }
                ),
                400,
            )
        if not isinstance(user_inst, Manager):
            return (
                jsonify({"message": "Only a manager can see all order's history."}),
                400,
            )
        try:
            res = user_inst.get_all_orders()
            if not res:
                return (
                    jsonify(
                        {
                            "message": "There are no orders at all in the order's history."
                        }
                    ),
                    200,
                )
            return jsonify({"your orders history": res}), 200
        except Exception as es:
            return jsonify({"message": f"Error showing orders history: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Connection error: {es}"}), 500


@app.route("/add_item_to_cart", methods=["PUT"])
def add_item_to_cart():
    """
    Add a specified furniture item to a user's shopping cart.

    This endpoint processes a JSON payload to identify the user, confirm they
    are logged in and of type User, and then add the requested furniture item
    to their shopping cart. The furniture object is created based on
    attributes such as 'color', 'material', 'is_adjustable', and 'has_armrest',
    if applicable.

    Required Fields:
        email (str): The email of the logged-in user (must be a User instance).
        object_type (str): The type of furniture (e.g., 'chair', 'table').
        item (dict): A dictionary containing item details, including 'color' and
                     properties specific to the furniture type (e.g., 'material'
                     for tables, 'is_adjustable' or 'has_armrest' for chairs).

    Optional Fields:
        amount (int): The number of items to add. Defaults to 1 if not provided.

    Returns:
        flask.Response: A JSON response with:
            - A success message and an optional advertisement (HTTP 200) if the
              item is successfully added to the cart.
            - An error message (HTTP 400) if the user is not logged in or is
              disconnected, or if the user is not of type User.
            - An error message (HTTP 404) if the specified furniture cannot be
              found.
            - A message indicating that the addition failed (HTTP 200) in case
              of insufficient stock or other constraints.
            - A server error message (HTTP 500) if any unexpected exception
              occurs during the process.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        email = data.get("email")
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to add furniture to your shopping cart."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You have been disconnected from the site."
                        "Please reconnect and try again."
                    }
                ),
                400,
            )
        if not isinstance(user_inst, User):
            return (
                jsonify({"message": "Only a user can add furniture to shopping cart."}),
                400,
            )
        try:
            amount = data.get("amount", 1)
            object_type = data.get("object_type")
            item = data.get("item")
            color = item["color"]
            furniture_factory = FurnitureFactory()

            if "table" in item:
                material = item["table"]["material"]
                item_object = furniture_factory.create_furniture(
                    furniture_type=object_type, color=color, material=material
                )

            if "chair" in item:
                is_adjustable = item["chair"]["is_adjustable"]
                has_armrest = item["chair"]["has_armrest"]
                item_object = furniture_factory.create_furniture(
                    furniture_type=object_type,
                    color=color,
                    is_adjustable=is_adjustable,
                    has_armrest=has_armrest,
                )

            if not item_object:
                return (
                    jsonify(
                        {
                            "message": "There is no furniture that has "
                            "the characteristics you specified."
                        }
                    ),
                    404,
                )
            res, advertisement = user_inst.cart.add_item(
                furniture=item_object, amount=amount
            )
            if not res:
                return (
                    jsonify(
                        {
                            "message": "This piece of furniture cannot be "
                            "added to the shopping cart."
                            "Probably due to stock shortages."
                        }
                    ),
                    200,
                )
            return (
                jsonify(
                    {
                        "message": "The addition to the shopping cart "
                        "was completed successfully!",
                        "advertisement": advertisement,
                    }
                ),
                200,
            )
        except Exception as es:
            return jsonify({"message": f"Error adding item to cart: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Connection error: {es}"}), 500


@app.route("/remove_item_from_cart", methods=["DELETE"])
def remove_item_from_cart():
    """
    Remove a specified furniture item from a user's shopping cart.

    This endpoint processes a JSON payload to identify the user, confirm
    they are logged in and of type User, and then remove the requested
    furniture item from their shopping cart. The furniture object is built
    based on attributes such as 'color', 'material', 'is_adjustable', and
    'has_armrest', if applicable.

    Required Fields:
        email (str): The email of the logged-in user (must be a User).
        object_type (str): The type of furniture (e.g., 'chair', 'table').
        item (dict): A dictionary containing item details, including 'color'
                     and properties specific to the furniture type (e.g.,
                     'material' for tables, 'is_adjustable' or 'has_armrest'
                     for chairs).

    Returns:
        flask.Response: A JSON response indicating one of the following:
            - A success message (HTTP 200) if the item is successfully removed
              from the cart.
            - An error message (HTTP 400) if the user is not logged in, is
              disconnected, or is not of type User.
            - An error message (HTTP 404) if the specified furniture item cannot
              be found based on the provided characteristics.
            - A message (HTTP 400) if removal is not possible (e.g., the item is
              not in the user's cart).
            - A server error message (HTTP 500) if an unexpected exception
              occurs during the process.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        email = data.get("email")
        if email not in cache_store:
            return (
                jsonify(
                    {
                        "message": "You must be logged in to "
                        "remove furniture from your shopping cart."
                        "please log in and than try again."
                    }
                ),
                400,
            )
        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "You have been disconnected from the site."
                        "Please reconnect and try again."
                    }
                ),
                400,
            )
        if not isinstance(user_inst, User):
            return (
                jsonify(
                    {
                        "message": "Only a user can remove furniture from his shopping cart."
                    }
                ),
                400,
            )
        try:
            object_type = data.get("object_type")
            item = data.get("item")
            color = item["color"]
            furniture_factory = FurnitureFactory()

            if "table" in item:
                material = item["table"]["material"]
                item_object = furniture_factory.create_furniture(
                    furniture_type=object_type, color=color, material=material
                )

            if "chair" in item:
                is_adjustable = item["chair"]["is_adjustable"]
                has_armrest = item["chair"]["has_armrest"]
                item_object = furniture_factory.create_furniture(
                    furniture_type=object_type,
                    color=color,
                    is_adjustable=is_adjustable,
                    has_armrest=has_armrest,
                )

            if not item_object:
                return (
                    jsonify(
                        {
                            "message": "There is no furniture that "
                            "has the characteristics you specified."
                        }
                    ),
                    404,
                )
            res = user_inst.cart.remove_item(furniture=item_object)
            if not res:
                return (
                    jsonify(
                        {
                            "message": "Removing the furniture from "
                            "the shopping cart is not possible. "
                            "It is probably not in your shopping cart."
                        }
                    ),
                    400,
                )
            return (
                jsonify(
                    {
                        "message": "Removing the furniture from the shopping "
                        "cart was successfully completed."
                    }
                ),
                200,
            )
        except Exception as es:
            return jsonify({"message": f"Error removing item from cart: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Connection error: {es}"}), 500


@app.route("/checkout", methods=["POST"])
def checkout_endpoint():
    """
    Perform a checkout operation for a logged-in user.

    This endpoint requires a JSON payload containing at least the user's
    email and credit card number. Optionally, a coupon code can be
    provided. The user must be logged in and identified in the cache_store.
    If the user is valid and the checkout succeeds, a success message is
    returned; otherwise, an error message is provided.

    Required Fields:
        email (str): The email of the logged-in user.
        credit_card_num (str): The user's credit card number.

    Optional Fields:
        coupon_code (str): A coupon code for possible discounts.

    Returns:
        flask.Response:
            - A success message (HTTP 200) if checkout completes.
            - An error message (HTTP 400) if the user is invalid or the checkout fails.
            - A server error message (HTTP 500) if an unexpected error occurs.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        email = data.get("email")
        if email not in cache_store:
            return (
                jsonify({"message": "User must be logged in to perform checkout."}),
                400,
            )

        user_inst = cache_store.get(email)
        if not user_inst or not isinstance(user_inst, User):
            return jsonify({"message": "Invalid user."}), 400

        credit_card_num = data.get("credit_card_num")
        coupon_code = data.get("coupon_code", None)

        success, msg = user_inst.checkout(credit_card_num, coupon_code)
        if success:
            return jsonify({"message": msg}), 200
        else:
            return jsonify({"message": msg}), 400

    except Exception as e:
        return jsonify({"message": f"Error in checkout process: {e}"}), 500


@app.route("/get_total_price", methods=["GET"])
def get_total_price_of_cart():
    """
    Calculate and return the total price of a user's shopping cart.

    This endpoint retrieves a user's total cart price. Optionally, if a valid
    coupon code is provided, a discount is applied. The user must be logged in
    (present in the cache_store) and must be an instance of User.

    Query Parameters:
        email (str): The email of the logged-in user.
        coupon_code (str, optional): A coupon code to apply a discount.

    Returns:
        flask.Response:
            - A JSON response with the total price (HTTP 200) if successful.
            - An error message (HTTP 400) if the user is not logged in, not found,
              or is not a User instance.
            - A server error message (HTTP 500) if any unexpected exception occurs.
    """
    try:
        email = request.args.get("email")
        coupon_code = request.args.get("coupon_code", None)
        if not email or email not in cache_store:
            return jsonify({"message": "User must be logged in."}), 400

        user_inst = cache_store.get(email)
        if not user_inst:
            return jsonify({"message": "User not found."}), 400

        if not isinstance(user_inst, User):
            return (
                jsonify({"message": "Only a user can view the shopping cart."}),
                400,
            )
        if (coupon_code is None) or (not coupon_code):
            total_price = user_inst.cart.get_total_price()
            return jsonify({"total_price": total_price}), 200

        if not isinstance(coupon_code, str):
            return (
                jsonify({"message": "coupon code must be str."}),
                400,
            )
        else:
            discount_percent, coupon_id = user_inst.cart.get_coupon_discount_and_id(
                coupon_code
            )
            total_price = user_inst.cart.apply_discount(discount_percent)
            return jsonify({"total_price": total_price}), 200

    except Exception as e:
        return jsonify({"message": f"Error retrieving total price: {e}"}), 500


@app.route("/get_user_info", methods=["GET"])
def get_user_info():
    """
    Retrieve basic information about a logged-in user or manager.

    This endpoint expects a query parameter 'email'. If the user or manager
    corresponding to that email is not in cache_store or not found, an error
    message is returned. Otherwise, a string representation of the user's
    or manager's information is provided.

    Query Parameters:
        email (str): The email of the logged-in user or manager.

    Returns:
        flask.Response:
            - A JSON response with the user's or manager's information (HTTP 200)
              if found.
            - An error message (HTTP 400) if the user/manager is not logged in
              or is not found in cache_store.
            - A server error message (HTTP 500) if an exception occurs.
    """
    try:
        email = request.args.get("email")
        if not email or email not in cache_store:
            return jsonify({"message": "User or Manager must be logged in."}), 400
        user_inst = cache_store.get(email)
        if not user_inst:
            return jsonify({"message": "User not found."}), 400
        ans = user_inst.__repr__()
        return jsonify({"user_info": ans}), 200
    except Exception as e:
        return (
            jsonify({"message": f"EError while retrieving user information: {e}"}),
            500,
        )


@app.route("/delete_user", methods=["DELETE"])
def delete_user():
    """
    Delete a user from the system by a logged-in manager.

    This endpoint requires a JSON payload containing two email addresses:
    - 'email': The manager's email, which must be a logged-in manager in the
      cache_store.
    - 'email_to_delete': The user or manager account to be deleted.

    Returns:
        flask.Response:
            - A JSON response (HTTP 200) indicating that the user was
              successfully deleted.
            - An error message (HTTP 400) if the manager is not logged in, if
              the email address is missing, or if the current user is not a
              manager.
            - A server error message (HTTP 500) for any unexpected exception.
    """
    try:
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify({"error": "No email provided"}), 400

        email = data["email"]
        email_to_delete = data["email_to_delete"]

        if email not in cache_store:
            return (
                jsonify({"message": "Only a logged-in manager can delete users."}),
                400,
            )

        user_inst = cache_store.get(email)
        if not isinstance(user_inst, Manager):
            return jsonify({"message": "Only a manager can delete users."}), 400

        MAIN_MANAGER.delete_user(email_to_delete)
        return (
            jsonify(
                {"message": f"User with email {email_to_delete} deleted successfully."}
            ),
            200,
        )

    except ValueError:
        return jsonify({"message": "Error deleting user: user not found"}), 400
    except Exception as e:
        return jsonify({"message": f"Error in delete user: {e}"}), 500


@app.route("/update_password", methods=["PUT"])
def update_password():
    """
    Update the password of a logged-in user or manager.

    This endpoint expects a JSON payload containing the following keys:
        - email (str): The email of the logged-in user or manager.
        - new_password (str): The new password to be set.

    The user or manager must be in the cache_store to proceed with the update.


    Returns:
        flask.Response:
            - HTTP 200 with a success message if the password was updated.
            - HTTP 400 if the user is not logged in, disconnected, or if there's a
              type-related error (TypeError).
            - HTTP 404 if a ValueError is raised, such as not finding the user.
            - HTTP 500 for any unexpected server errors.
    """

    try:
        data = request.get_json()
        if not data or "email" not in data or "new_password" not in data:
            return jsonify({"error": "Email and new password are required"}), 400

        email = data["email"]
        new_password = data["new_password"]

        if email not in cache_store:
            return (
                jsonify({"message": "You must be logged in to change your password."}),
                400,
            )

        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {"message": "You have been disconnected. Please log in again."}
                ),
                400,
            )

        try:
            user_inst.set_password(new_password)
            return jsonify({"message": "Password updated successfully"}), 200
        except TypeError as e:
            return jsonify({"error": str(e)}), 400
        except ValueError as e:
            return jsonify({"error": str(e)}), 404
        except Exception as e:
            return jsonify({"error": f"Error updating password: {e}"}), 500

    except Exception as e:
        return jsonify({"message": f"Connection error: {e}"}), 500


@app.route("/update_order_status", methods=["PUT"])
def update_order_status():
    """
    Update the status of an order, only accessible by a logged-in manager.

    This endpoint expects a JSON payload containing:
        - email (str): The manager's email address (must be logged in).
        - order_id (str or int): The ID of the order to update.

    Returns:
        flask.Response:
            - HTTP 200 with a success message if the order status was updated.
            - HTTP 400 if validation fails (e.g., no data, invalid email, manager
              not logged in) or if a ValueError is raised (e.g., order not found).
            - HTTP 403 if the user is logged in but is not a Manager.
            - HTTP 500 for any unexpected server errors.
    """
    try:
        data = request.get_json()
        if not data or "email" not in data or "order_id" not in data:
            return jsonify({"error": "Email and order ID are required"}), 400

        email = data["email"]
        order_id = data["order_id"]

        if email not in cache_store:
            return (
                jsonify(
                    {"message": "Only a logged-in manager can update order status."}
                ),
                400,
            )

        user_inst = cache_store.get(email)
        if not user_inst:
            return (
                jsonify(
                    {"message": "You have been disconnected. Please log in again."}
                ),
                400,
            )

        if not isinstance(user_inst, Manager):
            return jsonify({"message": "Only a manager can update order status."}), 403

        try:
            user_inst.update_order_status(order_id)
            return (
                jsonify({"message": f"Order {order_id} status updated successfully"}),
                200,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Error updating order status: {e}"}), 500

    except Exception as e:
        return jsonify({"message": f"Connection error: {e}"}), 500


@app.route("/apply_tax_on_user", methods=["PUT"])
def apply_tax_on_user():
    """
    Allows a logged-in manager to apply a tax rate to a user's shopping cart.

    Required Fields:
        manager_email (str): The email of the logged-in manager.
        user_email (str): The email of the user to whom the tax will be applied.
        tax_rate (int): The integer tax rate to apply.

    Returns:
        flask.Response:
            - HTTP 200 with a success message if the tax was applied successfully.
            - HTTP 400 with an error message if any validations fail
              (e.g., not logged in, invalid user, not a manager, invalid tax_rate).
            - HTTP 500 with an error message if there's an unexpected exception.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        manager_email = data.get("manager_email")
        user_email = data.get("user_email")
        tax_rate = data.get("tax_rate")

        if not manager_email or manager_email not in cache_store:
            return (
                jsonify(
                    {"message": "You must be logged in as a manager to apply tax."}
                ),
                400,
            )

        manager_inst = cache_store.get(manager_email)
        if not isinstance(manager_inst, Manager):
            return (
                jsonify({"message": "Only a manager can apply tax to a user's cart."}),
                403,
            )

        if not user_email or user_email not in cache_store:
            return (
                jsonify({"message": "User email not found or user is not logged in."}),
                400,
            )

        user_inst = cache_store.get(user_email)
        if not user_inst or not isinstance(user_inst, User):
            return (
                jsonify(
                    {"message": "Invalid user. Only a regular user can have a cart."}
                ),
                400,
            )

        try:
            tax_rate = int(tax_rate)

        except (TypeError, ValueError):
            return (
                jsonify({"message": "Tax rate must be an integer."}),
                400,
            )

        success = user_inst.cart.apply_tax_on_cart(tax_rate)
        if not success:
            return jsonify({"message": "Tax application failed."}), 500

        return (
            jsonify({"message": f"Tax rate of {tax_rate}% applied successfully."}),
            200,
        )

    except Exception as e:
        return jsonify({"message": f"Error applying tax: {e}"}), 500


@app.route("/add_credit_to_user", methods=["PUT"])
def add_credit_to_user():
    """
    Allows a logged-in manager to add credit to a user's account.

    Required Fields:
        manager_email (str): The email of the logged-in manager.
        user_email (str): The email of the user whose credit will be updated.
        credit (float or int): The amount of credit to add (can be negative to reduce credit).

    Returns:
        flask.Response:
            - A JSON response (HTTP 200) indicating success if the credit was updated.
            - A JSON response (HTTP 400) if any validations fail
              (e.g., manager not logged in, user not found, invalid user type, invalid credit).
            - A JSON response (HTTP 500) for any unexpected exceptions.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        manager_email = data.get("manager_email")
        user_email = data.get("user_email")
        credit = data.get("credit")

        if not manager_email or manager_email not in cache_store:
            return (
                jsonify(
                    {"message": "You must be logged in as a manager to add credit."}
                ),
                400,
            )
        manager_inst = cache_store.get(manager_email)
        if not isinstance(manager_inst, Manager):
            return (
                jsonify(
                    {"message": "Only a manager can add credit to a user's account."}
                ),
                403,
            )

        if not user_email or user_email not in cache_store:
            return (
                jsonify({"message": "User email not found or user is not logged in."}),
                400,
            )

        user_inst = cache_store.get(user_email)
        if not user_inst or not isinstance(user_inst, User):
            return (
                jsonify(
                    {"message": "Invalid user. Only a regular user can receive credit."}
                ),
                400,
            )
        try:
            credit = int(credit)

        except (TypeError, ValueError):
            return (
                jsonify({"message": "credit must be an integer."}),
                400,
            )

        user_inst.update_credit(credit)
        return (
            jsonify(
                {"message": f"Successfully updated {user_email}'s credit by {credit}."}
            ),
            200,
        )

    except ValueError as ve:
        return jsonify({"message": f"Error updating credit: {ve}"}), 400
    except Exception as e:
        return jsonify({"message": f"Unexpected error: {e}"}), 500
