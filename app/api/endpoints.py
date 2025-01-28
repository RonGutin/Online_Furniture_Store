from flask import Blueprint, jsonify, request

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
