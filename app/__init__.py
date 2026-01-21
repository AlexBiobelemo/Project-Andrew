"""
Initialize the Flask application and its extensions for CommunityWatch.
"""

from flask import Flask, request, session, current_app, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from authlib.integrations.flask_client import OAuth
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'
scheduler = APScheduler()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
babel = Babel()
oauth = OAuth()
csrf = CSRFProtect()


def dynamic_key_func():
    """Dynamic key function that considers user behavior."""
    from app.rate_limiting import user_or_ip_key
    return user_or_ip_key()


def create_app(config_class=Config):
    """
    Create and configure a Flask application instance.

    Args:
        config_class: The configuration class to use (defaults to Config).

    Returns:
        Flask: Configured Flask application instance.
    """
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Security settings for HTTPS
    # In debug mode, disable secure cookies to allow HTTP connections
    # In production, these should be True with proper HTTPS setup
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'http'

    # HTTPS Enforcement with HSTS - removed to prevent SSL-related errors
    # The development server runs on HTTP only to avoid SSL handshake errors

    # Validate configuration
    config_class.validate(app)

    # Define locale selector BEFORE initializing Babel
    def get_locale():
        return session.get('lang', request.accept_languages.best_match(app.config['LANGUAGES']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    oauth.init_app(app)
    csrf.init_app(app)

    # Initialize custom cache
    from app.cache import cache
    app.extensions['cache'] = cache
    # Store limiter in app extensions
    app.extensions['limiter'] = limiter
    app.extensions['csrf'] = csrf

    # Register OAuth clients
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    if app.config.get('FACEBOOK_CLIENT_ID') and app.config.get('FACEBOOK_CLIENT_SECRET'):
        oauth.register(
            name='facebook',
            client_id=app.config['FACEBOOK_CLIENT_ID'],
            client_secret=app.config['FACEBOOK_CLIENT_SECRET'],
            api_base_url='https://graph.facebook.com/v18.0/',
            access_token_url='https://graph.facebook.com/v18.0/oauth/access_token',
            authorize_url='https://www.facebook.com/v18.0/dialog/oauth',
            client_kwargs={'scope': 'email'}
        )

    # Import User model and define user_loader for Flask-Login
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        """
        Load a user from the database by their ID for Flask-Login.

        Args:
            user_id: The ID of the user to load (stored in session).

        Returns:
            User: The User object, or None if not found.
        """
        return db.session.get(User, int(user_id))

    # Configure scheduler for non-debug, non-testing environments
    if not app.debug and not app.testing:
        if not scheduler.running:
            scheduler.init_app(app)
            scheduler.start()

            # Schedule cleanup task
            from app.tasks import delete_old_issues, update_priorities
            if not scheduler.get_job('delete_old_issues_job'):
                scheduler.add_job(
                    id='delete_old_issues_job',
                    func=lambda: delete_old_issues(app),
                    trigger='interval',
                    days=1,
                    replace_existing=True
                )
            if not scheduler.get_job('update_priorities_job'):
                scheduler.add_job(
                    id='update_priorities_job',
                    func=lambda: update_priorities(app),
                    trigger='interval',
                    hours=6,  # Update every 6 hours
                    replace_existing=True
                )

    # Register blueprints
    from app.routes import bp as main_bp
    from app.api import api_v1, api_v2
    app.register_blueprint(main_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(api_v2)

    # Import models
    from app import models

    # Add behavior tracking after request
    @app.after_request
    def track_behavior(response):
        """Track user behavior after each request."""
        try:
            from app.rate_limiting import (
                should_track_behavior,
                calculate_suspicious_score,
                track_user_behavior
            )

            if should_track_behavior(request.endpoint or '', request.method, response.status_code):
                suspicious_score = calculate_suspicious_score(
                    request.endpoint or '',
                    request.method,
                    response.status_code,
                    request.headers.get('User-Agent', '')
                )
                track_user_behavior(response.status_code, suspicious_score)

        except Exception as e:
            current_app.logger.warning(f"Failed to track behavior: {e}")

        return response

    # Initialize gamification data
    with app.app_context():
        from app.utils import initialize_gamification
        initialize_gamification()

    # Custom Jinja2 filter for formatting dates
    @app.template_filter('strftime')
    def format_datetime(timestamp, fmt='%B %d, %Y'):
        """
        Format a timestamp for display in templates.

        Args:
            timestamp: Unix timestamp or datetime object.
            fmt: Format string for strftime (default: '%B %d, %Y').

        Returns:
            str: Formatted date string or "N/A" if timestamp is None.
        """
        if timestamp is None:
            return "N/A"
        if isinstance(timestamp, datetime):
            return timestamp.strftime(fmt)
        return datetime.fromtimestamp(timestamp).strftime(fmt)


    return app
