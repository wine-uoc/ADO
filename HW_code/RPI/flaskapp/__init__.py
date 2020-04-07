from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    """Construct the application."""
    app = Flask(__name__,
                instance_relative_config=False,
                template_folder="templates",
                static_folder="static"
                )

    # Configure the app from file
    app.config.from_object('config.Config')

    # Initialize plugins
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Import parts of the application
        from . import routes
        from . import auth

        # Register blueprints
        app.register_blueprint(routes.main_bp)
        app.register_blueprint(auth.auth_bp)

        # Create db
        db.create_all()

        return app
