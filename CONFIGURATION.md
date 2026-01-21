# Configuration Guide

This document details all configuration options available in CommunityWatch, including environment variables, Flask config, and runtime settings.

## Environment Variables

### Core Flask Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `run.py` | Entry point for Flask application |
| `FLASK_ENV` | `production` | Environment (development, testing, production) |
| `SECRET_KEY` | Required | Secret key for sessions and CSRF protection |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///app.db` | Database connection URL |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | Track object modifications (performance impact) |

**Database URL Formats:**
- SQLite: `sqlite:///app.db`
- PostgreSQL: `postgresql://user:password@localhost/dbname`
- MySQL: `mysql://user:password@localhost/dbname`

### AI Services Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | Required | Google Gemini API key for AI features |

### OAuth Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | None | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | None | Google OAuth client secret |
| `FACEBOOK_CLIENT_ID` | None | Facebook OAuth client ID |
| `FACEBOOK_CLIENT_SECRET` | None | Facebook OAuth client secret |

### File Upload Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_FOLDER` | `app/static/uploads` | Directory for uploaded files |
| `MAX_CONTENT_LENGTH` | `16MB` | Maximum file upload size |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_COOKIE_SECURE` | `False` in dev, `True` in prod | HTTPS-only session cookies |
| `REMEMBER_COOKIE_SECURE` | `False` in dev, `True` in prod | HTTPS-only remember cookies |
| `SESSION_COOKIE_HTTPONLY` | `True` | Prevent JavaScript access to session cookies |
| `REMEMBER_COOKIE_HTTPONLY` | `True` | Prevent JavaScript access to remember cookies |

### Internationalization

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGUAGES` | `['en', 'fr', 'es']` | Supported languages |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `DUPLICATE_DETECTION_RADIUS` | `0.005` | Radius for duplicate detection (~500m) |
| `ENABLE_CACHING` | `True` | Enable Redis caching |
| `CACHE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |

## Flask Configuration Class

The `Config` class in `config.py` provides additional configuration options.

### Database Settings

```python
class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f'sqlite:///{os.path.join(BASE_DIR, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Security Settings

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
```

### Upload Settings

```python
class Config:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
```

### Pagination Settings

```python
class Config:
    POSTS_PER_PAGE = 10
    ISSUES_PER_PAGE = 50
    NOTIFICATIONS_PER_PAGE = 15
```

### Rate Limiting Settings

```python
class Config:
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STRATEGY = "fixed-window"
```

### Email Settings (Future)

```python
class Config:
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
```

## Runtime Configuration

### Application Factory

The `create_app()` function in `app/__init__.py` configures the application based on the config class.

**Usage:**
```python
from app import create_app

app = create_app()  # Uses Config class
app = create_app('config.DevelopmentConfig')  # Custom config
```

### Configuration Classes

#### Development Configuration

```python
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
```

#### Testing Configuration

```python
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
```

#### Production Configuration

```python
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
```

## Environment-Specific Settings

### Development Environment

Create `.env.development`:
```bash
FLASK_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///dev.db
GEMINI_API_KEY=your_dev_key
```

### Production Environment

Create `.env.production`:
```bash
FLASK_ENV=production
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/db
GEMINI_API_KEY=your_prod_key
SECRET_KEY=your-production-secret-key
```

### Testing Environment

Create `.env.testing`:
```bash
FLASK_ENV=testing
DATABASE_URL=sqlite:///:memory:
TESTING=True
```

## Configuration Validation

The `Config.validate()` method checks for required settings:

```python
@classmethod
def validate(cls, app):
    errors = []
    if not cls.SECRET_KEY or cls.SECRET_KEY == 'default-secret-key':
        errors.append("SECRET_KEY is missing or using insecure default")
    if not cls.GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is missing")
    if errors:
        raise RuntimeError("; ".join(errors))
```

## Dynamic Configuration

### Runtime Settings

Some settings can be modified at runtime:

```python
# In Flask shell or application code
from flask import current_app

# Modify rate limiting
current_app.config['RATELIMIT_DEFAULT'] = "100 per hour"

# Change upload limits
current_app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
```

### Blueprint-Specific Configuration

Blueprints can have their own configuration:

```python
# In api.py
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
```

## Security Considerations

### Secret Key Management

- Never commit secret keys to version control
- Use different keys for each environment
- Rotate keys periodically
- Store production keys in secure vaults (AWS Secrets Manager, etc.)

### Database Credentials

- Use strong passwords
- Restrict database user permissions
- Use connection pooling
- Encrypt credentials in production

### API Keys

- Store AI service keys securely
- Monitor API usage and costs
- Implement key rotation
- Use environment variables, not config files

## Monitoring Configuration

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/communitywatch.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('CommunityWatch startup')
```

### Metrics and Monitoring

Configure monitoring endpoints:

```python
# Prometheus metrics (future)
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

## Troubleshooting Configuration Issues

### Common Problems

1. **Missing Environment Variables**
   - Check `.env` file exists and is loaded
   - Verify variable names match exactly
   - Use `print(os.environ)` to debug

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Test connection manually
   - Check firewall and network settings

3. **File Upload Problems**
   - Ensure UPLOAD_FOLDER exists and is writable
   - Check file permissions
   - Verify MAX_CONTENT_LENGTH setting

4. **OAuth Configuration**
   - Register application with OAuth provider
   - Verify redirect URIs match
   - Check client secrets are correct

### Configuration Debugging

Enable debug logging to troubleshoot config issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Log configuration loading
app.logger.debug(f"DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
app.logger.debug(f"SECRET_KEY set: {bool(app.config['SECRET_KEY'])}")
```

### Configuration Testing

Test configuration in Flask shell:

```bash
flask shell
```

```python
from app import create_app
app = create_app()
print(app.config['SECRET_KEY'])
print(app.config['SQLALCHEMY_DATABASE_URI'])
```

## Best Practices

1. **Environment Separation**: Use different configs for dev/test/prod
2. **Secret Management**: Never commit secrets to version control
3. **Validation**: Always validate critical configuration
4. **Documentation**: Document all configuration options
5. **Monitoring**: Log configuration changes and errors
6. **Security**: Use HTTPS and secure cookie settings in production
7. **Performance**: Configure caching and connection pooling
8. **Scalability**: Plan for horizontal scaling with config