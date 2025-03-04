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
