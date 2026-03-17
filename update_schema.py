from app import create_app
from extensions import db
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def update_schema():
    """
    Adds missing columns for book images and last_reminder_at.
    """
    with app.app_context():
        try:
            # 1. Add image_file to books
            logger.info("Checking for 'image_file' in 'books' table...")
            check_image_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='books' AND column_name='image_file';
            """)
            result = db.session.execute(check_image_sql).fetchone()

            if not result:
                logger.info("Adding 'image_file' to 'books'...")
                db.session.execute(text("ALTER TABLE books ADD COLUMN image_file VARCHAR(100) DEFAULT 'default.jpg' NOT NULL;"))
                db.session.commit()
                logger.info("✅ Column 'image_file' added.")
            else:
                logger.info("ℹ️ Column 'image_file' already exists.")

            # 2. Add last_reminder_at to borrowed_books
            logger.info("Checking for 'last_reminder_at' in 'borrowed_books' table...")
            check_reminder_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='borrowed_books' AND column_name='last_reminder_at';
            """)
            result = db.session.execute(check_reminder_sql).fetchone()

            if not result:
                logger.info("Adding 'last_reminder_at' to 'borrowed_books'...")
                db.session.execute(text("ALTER TABLE borrowed_books ADD COLUMN last_reminder_at TIMESTAMP WITH TIME ZONE;"))
                db.session.commit()
                logger.info("✅ Column 'last_reminder_at' added.")
            else:
                logger.info("ℹ️ Column 'last_reminder_at' already exists.")

            print("\n🚀 Database schema update complete!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Update failed: {e}")
            raise e

if __name__ == "__main__":
    update_schema()
