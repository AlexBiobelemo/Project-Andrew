# Developer Setup Guide

This guide provides detailed instructions for setting up CommunityWatch for development, including troubleshooting common issues.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **PostgreSQL**: Version 12 or higher
- **Git**: Version control system
- **Node.js**: Version 14+ (optional, for frontend development)

### Hardware Requirements

- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: 5GB free space
- **Internet**: Stable connection for downloading dependencies

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/AlexBiobelemo/Project-Andrew-CommunityWatch-/tree/main/Version%202
   cd communitywatch
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**
   ```sql
   CREATE DATABASE communitywatch;
   CREATE USER communitywatch_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE communitywatch TO communitywatch_user;
   ```

6. **Initialize the database**
   ```bash
   flask db upgrade
   ```

7. **Run the application**
   ```bash
   flask run
   ```

Visit `http://localhost:5000` to see the application.

## Detailed Setup Instructions

### 1. Repository Setup

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/AlexBiobelemo/Project-Andrew-CommunityWatch-/tree/main/Version%202
cd communitywatch
```

### 2. Python Environment

Create and activate a virtual environment:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

Verify Python version:
```bash
python --version  # Should be 3.8+
```

### 3. Dependency Installation

Install Python packages:
```bash
pip install -r requirements.txt
```

If you encounter permission errors, try:
```bash
pip install --user -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://username:password@localhost/communitywatch

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret

# File Uploads
UPLOAD_FOLDER=app/static/uploads

# Duplicate Detection
DUPLICATE_DETECTION_RADIUS=0.005
```

### 5. PostgreSQL Setup

**Installation:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS (with Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from postgresql.org and follow the installer.

**Database Creation:**
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE communitywatch;
CREATE USER communitywatch_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE communitywatch TO communitywatch_user;
\q
```

### 6. Database Initialization

Set Flask environment variables:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
```

Initialize and migrate the database:
```bash
flask db init  # Only needed once
flask db migrate -m "Initial migration"
flask db upgrade
```

### 7. Initialize Gamification Data

Run the Flask shell to initialize badges and challenges:
```bash
flask shell
```

```python
from app.utils import initialize_gamification
initialize_gamification()
exit()
```

## Running the Application

### Development Server

```bash
flask run
```

The application will be available at `http://localhost:5000`.

### Debug Mode

For development with auto-reload:
```bash
FLASK_DEBUG=1 flask run
```

### Using the Run Script

Alternatively, use the provided run script:
```bash
python run.py
```

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `which python`

#### 2. Database Connection Errors

**Error:** `psycopg2.OperationalError: FATAL: password authentication failed`

**Solutions:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database credentials in `.env`
- Ensure user has proper permissions
- Test connection: `psql -U communitywatch_user -d communitywatch`

#### 3. Migration Errors

**Error:** `alembic.util.exc.CommandError: Can't locate revision`

**Solution:**
- Reset migrations: `rm -rf migrations/`
- Reinitialize: `flask db init`
- Create new migration: `flask db migrate`

#### 4. Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
- Kill process on port 5000: `lsof -ti:5000 | xargs kill -9`
- Or run on different port: `flask run -p 5001`

#### 5. Template Not Found

**Error:** `jinja2.exceptions.TemplateNotFound`

**Solution:**
- Ensure all template files exist in `app/templates/`
- Check file permissions
- Verify Flask app structure

#### 6. Static Files Not Loading

**Solution:**
- Ensure `app/static/` directory exists
- Check file permissions
- Clear browser cache
- Verify Flask static folder configuration

#### 7. AI Service Errors

**Error:** `AI service unavailable`

**Solutions:**
- Verify `GEMINI_API_KEY` in `.env`
- Check API quota limits
- Ensure internet connectivity
- Review AI service logs

#### 8. OAuth Configuration Issues

**Error:** `OAuth provider not configured`

**Solution:**
- Add OAuth credentials to `.env`
- Register application with OAuth provider
- Verify redirect URIs match

### Development Tools

#### Flask Shell

Access interactive shell for debugging:
```bash
flask shell
```

Common shell commands:
```python
from app import db
from app.models import User, Issue

# Query database
users = User.query.all()
issues = Issue.query.limit(5).all()

# Create test data
user = User(username='test', email='test@example.com')
user.set_password('password')
db.session.add(user)
db.session.commit()
```

#### Database Inspection

Check database contents:
```bash
psql -U communitywatch_user -d communitywatch
```

```sql
\d  -- List tables
SELECT COUNT(*) FROM user;
SELECT * FROM issue LIMIT 5;
```

#### Logging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check Flask logs in terminal or configure file logging in `config.py`.

### Performance Tuning

#### Database Optimization

- Ensure proper indexes exist
- Monitor slow queries with `EXPLAIN ANALYZE`
- Consider connection pooling for production

#### Caching

The application uses Flask-Caching. Configure Redis for better performance:

```bash
# Install Redis
sudo apt install redis-server

# Configure in .env
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python
- Pylance
- Flask Snippets
- SQLTools
- GitLens

#### PyCharm

- Configure interpreter to use virtual environment
- Enable Flask support
- Set up database connection for SQL inspection

## Contributing

### Code Style

Follow PEP 8 guidelines:
```bash
pip install flake8 black
flake8 app/
black app/
```

### Pre-commit Hooks

Set up pre-commit for automatic code quality checks:
```bash
pip install pre-commit
pre-commit install
```

### Testing

Write tests for new features:
```python
# app/tests/test_example.py
import pytest
from app import create_app, db

def test_example():
    app = create_app()
    with app.app_context():
        # Test code here
        assert True
```

Run tests: `pytest`

## Deployment

For production deployment, see `DEPLOYMENT.md`.

## Support

If you encounter issues not covered here:
1. Check the troubleshooting section in `README.md`
2. Search existing GitHub issues
3. Create a new issue with detailed information:
   - Error messages
   - Steps to reproduce
   - System information
   - Relevant logs