from flask import Flask
from config import DevelopmentConfig
from extensions import db, bcrypt, login_manager

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Import and register Blueprints
        from routes import main
        app.register_blueprint(main)
        
        # Import models to ensure they are registered
        import models

    return app

# Optional: Create a default app instance for simple usage
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
