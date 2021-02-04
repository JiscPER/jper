from flask_login import LoginManager

def setup_app(app):
    if app.config.get("ACCOUNT_ENABLE", False):
        print("Adding login_manager to app")
        login_manager = LoginManager()
        login_manager.init_app(app)

