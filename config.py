import os
import urllib.parse
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load from .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    """Development configuration using Supabase/Local connection string."""
    DEBUG = True
    # If DATABASE_URL is in .env, use it. Otherwise, default to local.
    # We ensure we handle the 'postgres://' vs 'postgresql://' fix often needed for some platforms.
    raw_uri = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/library_db')
    if raw_uri and raw_uri.startswith("postgres://"):
        raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = raw_uri

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    raw_uri = os.environ.get('DATABASE_URL')
    if raw_uri and raw_uri.startswith("postgres://"):
        raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = raw_uri

# Dictionary for easy application factory mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
