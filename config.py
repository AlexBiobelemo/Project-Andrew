"""
Configuration settings for the Flask application.
Loads environment variables and defines default values.
"""

import os
from dotenv import load_dotenv
from flask import current_app

# Base directory for the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Flask application configuration variables."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-super-secret-key-you-should-change')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f'sqlite:///{os.path.join(BASE_DIR, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # File uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'Uploads')

    # Pagination
    POSTS_PER_PAGE = 10

    # Duplicate detection
    DUPLICATE_DETECTION_RADIUS = float(os.environ.get('DUPLICATE_DETECTION_RADIUS', 0.005))  # ~500m default

    # Internationalization
    LANGUAGES = ['en', 'fr', 'es']

    # OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')

    # Security settings for HTTPS (set in create_app)

    @classmethod
    def validate(cls, app):
        """
        Validate critical configuration variables.

        Args:
            app: Flask application instance for logging.

        Raises:
            RuntimeError: If critical variables are missing or invalid in production.
        """
        with app.app_context():
            errors = []
            if not cls.SECRET_KEY or cls.SECRET_KEY == 'a-super-secret-key-you-should-change':
                errors.append("SECRET_KEY is missing or using insecure default")
                current_app.logger.error("Configuration error: SECRET_KEY is missing or using insecure default")
            if not cls.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY is missing")
                current_app.logger.error("Configuration error: GEMINI_API_KEY is missing")
            if errors:
                raise RuntimeError("; ".join(errors))
            current_app.logger.info("Configuration validated successfully")