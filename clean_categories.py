from app import create_app
from extensions import db
from models import Book
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def clean_categories():
    """
    Standardizes book categories in the database.
    Maps old/inconsistent values to the new fixed set:
    Technology, Arts, Literature, Science, History
    """
    category_map = {
        'tech': 'Technology',
        'technology': 'Technology',
        'science': 'Science',
        'lit': 'Literature',
        'literature': 'Literature',
        'arts': 'Arts',
        'art': 'Arts',
        'history': 'History',
        'hist': 'History',
        'general': 'Literature' # Default fallback
    }

    with app.app_context():
        try:
            books = Book.query.all()
            updated_count = 0
            
            for book in books:
                current_cat = book.category.lower().strip()
                if current_cat in category_map:
                    new_cat = category_map[current_cat]
                    if book.category != new_cat:
                        logger.info(f"Updating '{book.title}': '{book.category}' -> '{new_cat}'")
                        book.category = new_cat
                        updated_count += 1
                else:
                    # If not in map, title-case it as a best effort or default to Science/Tech
                    new_cat = book.category.title().strip()
                    # Final check against allowed list
                    allowed = ['Technology', 'Arts', 'Literature', 'Science', 'History']
                    if new_cat not in allowed:
                        new_cat = 'Technology' # Safe default for mismatched ones
                    
                    if book.category != new_cat:
                        logger.info(f"Normalizing '{book.title}': '{book.category}' -> '{new_cat}'")
                        book.category = new_cat
                        updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"✅ Successfully updated {updated_count} books.")
            else:
                logger.info("ℹ️ All books already match the standard category format.")
            
            print("\n🚀 Category cleanup complete!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Cleanup failed: {e}")
            raise e

if __name__ == "__main__":
    clean_categories()
