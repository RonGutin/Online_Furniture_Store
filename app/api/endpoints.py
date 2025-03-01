from flask import jsonify, request, Flask
from app.models.inventory import Inventory
from app.models.FurnitureFactory import FurnitureFactory
from app.models.Users import Authentication, Manager, User

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, Welcome to our shop!"


main_manager = Manager(email="hili@example.com", name="Hili", password="password4")


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
                        "message": "There is no object that has the characteristics you specified."
                    }
                ),
                404,
            )

        main_manager.update_inventory(item=item_object, quantity=quantity, sign=sign)
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
        name = data["name"]
        email = data["email"]
        password = data["password"]

        res = main_manager.add_manager(name=name, email=email, password=password)
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
            return (
                jsonify(
                    {
                        "user_data": res.to_dict_without_password(),
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
        password = request.args.get("password")
        auth = Authentication()
        user_inst = auth.sign_in(email=email, password=password)
        if isinstance(user_inst, Manager):
            return (
                jsonify(
                    {
                        "message": "You can see a shopping cart only as a user."
                        "you logged in as a manager. Please try again."
                    }
                ),
                400,
            )
        if not user_inst:
            return (
                jsonify(
                    {
                        "message": "Signing in failed,"
                        "You must be logged in to view your shopping cart."
                        "lease try to log in again."
                    }
                ),
                400,
            )
        try:
            res = user_inst.view_cart()
            return jsonify({"your shopping cart": res}), 200
        except Exception as es:
            return jsonify({"message": f"Error showing cart: {es}"}), 500
    except Exception as es:
        return jsonify({"message": f"Error while signing in: {es}"}), 500
