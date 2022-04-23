from .app import create as create_app
from .socketio import socketio

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=app.config["RUN_DEBUG"], host=app.config["APP_HOST"], port=app.config["APP_PORT"])
