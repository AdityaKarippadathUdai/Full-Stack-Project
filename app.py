import os
from flask import Flask
from config import DevelopmentConfig
from extensions import db, bcrypt, login_manager, mail

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with the app instance
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    with app.app_context():
        # Import and register Blueprints
        from routes import main
        app.register_blueprint(main)
        
        # Import models to ensure they are registered
        import models

    # ── Background Scheduler (auto-reminders) ────────────────────────────────
    # Guard: Flask's dev reloader launches two processes; only start in the
    # main process (or in production where WERKZEUG_RUN_MAIN is absent).
    import os
    if not app.config.get('TESTING') and os.environ.get('WERKZEUG_RUN_MAIN') != 'false':
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        from scheduler import send_auto_reminders
        import atexit

        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=send_auto_reminders,
            args=[app],
            trigger=IntervalTrigger(hours=6),
            id='auto_reminder_job',
            name='Send overdue book reminders',
            replace_existing=True
        )
        scheduler.start()
        # Ensure scheduler shuts down when the app exits
        atexit.register(lambda: scheduler.shutdown(wait=False))
        app.logger.info("✅ Auto-reminder scheduler started (every 6 hours).")
    # ─────────────────────────────────────────────────────────────────────────

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
            
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
