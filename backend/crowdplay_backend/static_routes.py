def register(app):
    @app.route("/<path:path>")  # catches all
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(e):
        # This flips the error condition and changes it to a success request
        # that returns the page that bootstraps the React application.
        # 404 will be handled in the client side.
        return app.send_static_file("index.html")
