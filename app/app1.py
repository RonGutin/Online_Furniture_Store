from flask import Flask
from app.api.endpoints import api_blueprint


def create_app() -> Flask:
    """
    Creates and configures the Flask application.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5005)
