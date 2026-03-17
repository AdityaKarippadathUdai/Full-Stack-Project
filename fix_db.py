from app import create_app
from extensions import db
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def sync_schema():
    """
    Safely adds missing columns to the borrowed_books table in PostgreSQL.
    """
    with app.app_context():
        try:
            # 1. Check if 'requested_at' exists
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='borrowed_books' AND column_name='requested_at';
            """)
            result = db.session.execute(check_sql).fetchone()

            if not result:
                logger.info("Column 'requested_at' is missing. Adding it now...")
                # Add the column. We allow NULL initially to avoid issues with existing data,
                # then we can populate it and set NOT NULL if needed.
                # However, for convenience in dev, we'll give it a default of NOW().
                add_col_sql = text("""
                    ALTER TABLE borrowed_books 
                    ADD COLUMN requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                """)
                db.session.execute(add_col_sql)
                db.session.commit()
                logger.info("✅ Column 'requested_at' added successfully!")
            else:
                logger.info("ℹ️ Column 'requested_at' already exists.")

            # 2. Check for 'status' column constraints/defaults if necessary
            # (In SQLAlchemy we changed the default, but the DB might need an update)
            logger.info("Checking 'status' column default...")
            alter_status_sql = text("""
                ALTER TABLE borrowed_books ALTER COLUMN status SET DEFAULT 'pending';
            """)
            db.session.execute(alter_status_sql)
            db.session.commit()
            logger.info("✅ 'status' column default set to 'pending'.")

            # 3. Fix NOT NULL constraints for borrow workflow
            logger.info("Dropping NOT NULL constraints on borrow_date and return_date...")
            drop_const_sql = text("""
                ALTER TABLE borrowed_books ALTER COLUMN borrow_date DROP NOT NULL;
                ALTER TABLE borrowed_books ALTER COLUMN return_date DROP NOT NULL;
            """)
            db.session.execute(drop_const_sql)
            db.session.commit()
            logger.info("✅ Date columns are now nullable.")

            print("\n🚀 Database synchronization complete!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Synchronization failed: {e}")
            raise e

if __name__ == "__main__":
    sync_schema()
