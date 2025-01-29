from flask import Blueprint, jsonify, request
from app.models.inventory import Inventory

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, Welcome to our shop!"})

@api_blueprint.route('/data', methods=['POST']) ### example - delete  this function
def handle_data():
    data = request.get_json()
    return jsonify({"received": data})

def register_endpoints(app):
    app.register_blueprint(api_blueprint, url_prefix='/api')


@api_blueprint.route('/update_quntity', methods=['GET'])
def update_quntity():
    try: # get info from url request
        furniture_type = request.args.get('furniture_type', type=int) 
        color = request.args.get('color', type=str)
        high = request.args.get('high', type=int)
        depth = request.args.get('depth', type=int)
        width = request.args.get('width', type=int)
        is_adjustable = request.args.get('is_adjustable', type=bool)
        has_armrest = request.args.get('has_armrest', type=bool)
        material = request.args.get('material', type=str)
        action = request.args.get('action', type=str) # regular user can send only '1'(buying = remove from inventory) (bool)
        quntity = request.args.get('quntity', type=str)
        inventory_object = Inventory()
        furniture_id = inventory_object.get_indx_furniture_by_values(furniture_type=furniture_type, color=color, high=high, depth=depth, width=width, is_adjustable=is_adjustable, has_armrest=has_armrest, material=material, inventory_object=inventory_object)
        if not furniture_id: 
            return jsonify({"error: DB connection failed"}), 500
        if furniture_id == -1:
            return jsonify({"error: Missing required parameters/there is no furniture with those params"}), 400
        if furniture_id:
            try:
                res = inventory_object.update_quntity(indx=furniture_id, action=action, quntity=quntity)
                if res:
                    return jsonify({"updating succsuss"}), 200
                if not res:
                    return jsonify({"error: Inventory updating failed"}), 500
            except Exception as e:
                return jsonify({"error": f"An error occurred: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

        



