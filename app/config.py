"""
Configuration settings for the Flask application.
Loads environment variables and defines default values.
"""

import os
from dotenv import load_dotenv
from flask import current_app

# Base directory for the application
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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
            if not app.debug:
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
            else:
                if cls.SECRET_KEY == 'a-super-secret-key-you-should-change':
                    current_app.logger.warning(
                        "Using default SECRET_KEY in debug mode; set a secure SECRET_KEY for production")