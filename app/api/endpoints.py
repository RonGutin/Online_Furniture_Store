from flask import jsonify, request, Flask
from app.models.inventory import Inventory
from app.models.FurnitureFactory import FurnitureFactory
from app.models.Users import Manager

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, Welcome to our shop!"


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

        manager = Manager(email="hili@example.com", name="Hili", password="password4")
        res = manager.update_inventory(item=item_object, quantity=quantity, sign=sign)
        return jsonify({"message": "Inventory updated successfully."}), 200

    except Exception as es:
        return jsonify({"message": f"Error updating Inventory: {es}"}), 500


@app.route("/get_furniture_info_by_price_range", methods=["GET"])
def get_furniture_info_by_price_range():
    max_price = float(request.args.get("max_price"))
    min_price = float(request.args.get("min_price"))
    inv = Inventory()
    res = inv.get_information_by_price_range(min_price=min_price, max_price=max_price)
    if res is None:
        return jsonify({"message": "Error while processing request"}), 500
    elif len(res) > 0:
        return res, 200
    return jsonify({"message": "There are no furnitures in this price range"}), 200
