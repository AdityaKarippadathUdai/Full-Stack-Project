import os
from dotenv import load_dotenv

# Load environment variables from a .env file located in the same directory
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    # Default to a local postgres database if DATABASE_URL is not set
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:AdityaProject2004#@db.rhhilfawcrqqaysrfpjf.supabase.co:5432/postgres')

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    # In production, require the DATABASE_URL to be set in the environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
