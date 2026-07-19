from app import create_app

flask_app = create_app()

if __name__ == "__main__":
    flask_app.run(
        host=flask_app.config.get("HOST", "127.0.0.1"),
        port=flask_app.config.get("PORT", 5000),
        debug=flask_app.config.get("DEBUG", True),
    )
