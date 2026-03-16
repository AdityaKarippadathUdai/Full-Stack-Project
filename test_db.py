from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

def test_connection():
    with app.app_context():
        try:
            # Execute a simple query to test connection
            db.session.execute(text('SELECT 1'))
            print("✅ Successfully connected to the Supabase database!")
            
            # Optionally create tables if they don't exist
            # print("Creating tables...")
            # db.create_all()
            # print("Tables created successfully!")
            
        except Exception as e:
            print(f"❌ Failed to connect to the database: {e}")

if __name__ == "__main__":
    test_connection()
