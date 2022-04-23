import os

from flasgger import Swagger
from flask import Flask

from .api_routes import api_v1
from .config import Config
from .db import db
from .logger import setLoggerConfig
from .socket_events import EnvNamespace
from .socketio import socketio
from .static_routes import register as static_routes


def create():
    app = Flask(__name__, template_folder="web", static_folder="web", static_url_path="")

    # App configuration
    config_class = os.environ.get("APP_SETTINGS") or "crowdplay_backend.config.Config"
    app.config.from_object(config_class)

    # Logger configuration
    setLoggerConfig(log_level=app.config["LOG_LEVEL"])

    # Database
    db.init_app(app)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite://"):
        with app.app_context():
            db.create_all()

    # Socket.IO and events
    socketio.init_app(app)
    socketio.on_namespace(EnvNamespace(Config.WS_NS))

    # Importing and registering Flask routes
    app.register_blueprint(api_v1)

    # Static routes
    static_routes(app)

    # Swagger UI
    Swagger(app)

    return app
