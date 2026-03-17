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
        
        # Ensure default admin exists with correct password
        from models import User
        admin = User.query.filter_by(email="admin@gmail.com").first()
        hashed_pw = bcrypt.generate_password_hash("12345678").decode('utf-8')
        
        if not admin:
            admin_user = User(
                name="Admin",
                email="admin@gmail.com",
                password=hashed_pw,
                phone="0000000000",
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created!")
        else:
            # Update password if it's different (optional but recommended here for the user's fix)
            admin.password = hashed_pw
            admin.role = 'admin'  # Ensure role is also correct
            db.session.commit()
            print("Admin credentials verified/updated.")
            
    app.run(debug=True, port=5000)
