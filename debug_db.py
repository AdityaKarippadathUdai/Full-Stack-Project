from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

def debug_schema():
    with app.app_context():
        try:
            print("--- Database Schema Inspection ---")
            
            # Query information_schema to see column properties
            sql = text("""
                SELECT column_name, is_nullable, column_default, data_type
                FROM information_schema.columns 
                WHERE table_name = 'borrowed_books'
                ORDER BY ordinal_position;
            """)
            
            rows = db.session.execute(sql).fetchall()
            
            print(f"{'Column':<20} | {'Nullable':<10} | {'Default':<20} | {'Type'}")
            print("-" * 75)
            for row in rows:
                print(f"{row.column_name:<20} | {row.is_nullable:<10} | {str(row.column_default):<20} | {row.data_type}")
            
            print("\n--- Testing Model Insertion ---")
            from models import BorrowedBook
            from datetime import datetime, timezone
            
            # Note: We won't actually commit this if it works, just testing session behavior
            # But the error usually happens at flush/commit time.
            test_record = BorrowedBook(
                user_id=1, # Assuming user 1 exists, or just testing object creation
                book_id=1, # Assuming book 1 exists
                status='pending',
                requested_at=datetime.now(timezone.utc)
            )
            print("✅ Successfully created BorrowedBook object with null dates.")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_schema()
