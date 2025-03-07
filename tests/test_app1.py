from unittest.mock import patch, MagicMock


def test_create_app():
    """Test the create_app function"""

    mock_flask = MagicMock()
    mock_blueprint = MagicMock()

    with patch("flask.Flask", return_value=mock_flask), patch(
        "app.api.endpoints.api_blueprint", mock_blueprint, create=True
    ):

        from app.app1 import create_app

        app = create_app()

        assert app == mock_flask
        mock_flask.register_blueprint.assert_called_once_with(
            mock_blueprint, url_prefix="/api"
        )
