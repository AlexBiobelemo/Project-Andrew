# Troubleshooting Guide

This guide provides solutions to common issues encountered when running CommunityWatch.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Database Problems](#database-problems)
3. [Application Startup Issues](#application-startup-issues)
4. [Runtime Errors](#runtime-errors)
5. [Performance Issues](#performance-issues)
6. [Security Issues](#security-issues)
7. [AI Service Problems](#ai-service-problems)
8. [Deployment Issues](#deployment-issues)
9. [Getting Help](#getting-help)

## Installation Issues

### Python Version Problems

**Error:** `Python 3.8+ required`

**Solutions:**
- Check Python version: `python --version`
- Install Python 3.8+: `sudo apt install python3.8` (Ubuntu)
- Use pyenv: `pyenv install 3.8.10 && pyenv global 3.8.10`
- Update PATH if needed

### Virtual Environment Issues

**Error:** `ModuleNotFoundError` after activating venv

**Solutions:**
- Ensure venv is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `which python`
- Recreate venv: `rm -rf venv && python -m venv venv`

### Dependency Installation Failures

**Error:** `Could not find a version that satisfies the requirement`

**Solutions:**
- Update pip: `pip install --upgrade pip`
- Use compatible versions from requirements.txt
- Install system dependencies:
  ```bash
  sudo apt install build-essential python3-dev
  ```
- Use `--only-binary=all` for problematic packages

## Database Problems

### Connection Refused

**Error:** `psycopg2.OperationalError: connection to server failed`

**Solutions:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection string in `.env`
- Test connection: `psql -U username -d database -h localhost`
- Check firewall: `sudo ufw status`
- Verify user permissions: `psql -c "\du"`

### Migration Failures

**Error:** `alembic.util.exc.CommandError`

**Solutions:**
- Reset migrations: `rm -rf migrations/ && flask db init`
- Check database schema manually
- Verify model definitions
- Run `flask db migrate` again
- Apply manually: `flask db upgrade`

### Data Corruption

**Symptoms:** Inconsistent data, missing records

**Solutions:**
- Check database logs: `tail -f /var/log/postgresql/postgresql-*.log`
- Run integrity checks: `vacuum analyze;`
- Restore from backup if available
- Check application logs for error patterns

## Application Startup Issues

### Import Errors

**Error:** `ImportError: No module named 'app'`

**Solutions:**
- Set FLASK_APP: `export FLASK_APP=run.py`
- Check file structure: `ls -la app/`
- Verify `__init__.py` exists in app directory
- Check Python path: `python -c "import sys; print(sys.path)"`

### Configuration Errors

**Error:** `RuntimeError: SECRET_KEY is missing`

**Solutions:**
- Create `.env` file with required variables
- Check variable names match config.py
- Verify file permissions: `chmod 600 .env`
- Use absolute paths where required

### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solutions:**
- Find process: `lsof -i :5000`
- Kill process: `kill -9 <PID>`
- Change port: `flask run -p 5001`
- Check for multiple instances

## Runtime Errors

### Template Not Found

**Error:** `jinja2.exceptions.TemplateNotFound`

**Solutions:**
- Verify template files exist: `ls app/templates/`
- Check file permissions
- Clear browser cache
- Check template inheritance

### Database Session Errors

**Error:** `sqlalchemy.exc.OperationalError`

**Solutions:**
- Check database connection
- Verify table schemas
- Handle connection timeouts
- Implement retry logic

### File Upload Issues

**Error:** `FileNotAllowed` or size errors

**Solutions:**
- Check UPLOAD_FOLDER permissions
- Verify file type restrictions
- Increase MAX_CONTENT_LENGTH if needed
- Check disk space: `df -h`

## Performance Issues

### Slow Page Loads

**Symptoms:** Pages take >3 seconds to load

**Solutions:**
- Check database query performance: `EXPLAIN ANALYZE SELECT ...`
- Enable caching: Configure Redis
- Optimize images and static files
- Check server resources: `top`, `htop`

### High Memory Usage

**Symptoms:** Application uses excessive RAM

**Solutions:**
- Monitor with `ps aux | grep flask`
- Reduce Gunicorn workers
- Enable connection pooling
- Check for memory leaks in code

### Database Performance

**Symptoms:** Slow queries, high CPU

**Solutions:**
- Add database indexes: `CREATE INDEX ...`
- Optimize queries: Use `select()` with `joinedload()`
- Enable query logging: `SQLALCHEMY_ECHO = True`
- Monitor with `pg_stat_statements`

## Security Issues

### CSRF Token Errors

**Error:** `The CSRF token is invalid`

**Solutions:**
- Ensure forms include `{{ csrf_token() }}`
- Check session configuration
- Verify SECRET_KEY is set
- Clear browser cookies

### Authentication Problems

**Symptoms:** Users can't login consistently

**Solutions:**
- Check session configuration
- Verify cookie settings
- Monitor for session fixation
- Check for concurrent session issues

### Rate Limiting Issues

**Error:** `429 Too Many Requests`

**Solutions:**
- Check rate limit configuration
- Verify user behavior tracking
- Adjust limits in `rate_limiting.py`
- Monitor for abuse patterns

## AI Service Problems

### Gemini API Errors

**Error:** `AI service unavailable`

**Solutions:**
- Check GEMINI_API_KEY in `.env`
- Verify API quota: https://makersuite.google.com/app/apikey
- Monitor API usage and costs
- Implement fallback mechanisms

### Embedding Generation Failures

**Symptoms:** Search features not working

**Solutions:**
- Check API connectivity
- Verify model availability
- Monitor token limits
- Implement caching for embeddings

### Content Moderation Issues

**Symptoms:** Inappropriate content not flagged

**Solutions:**
- Review AI prompts in `ai_services.py`
- Adjust moderation thresholds
- Implement manual review queue
- Monitor false positives/negatives

## Deployment Issues

### Nginx Configuration Problems

**Error:** `502 Bad Gateway`

**Solutions:**
- Check Gunicorn is running: `ps aux | grep gunicorn`
- Verify socket permissions
- Check Nginx error logs: `tail -f /var/log/nginx/error.log`
- Test upstream: `curl http://127.0.0.1:8000`

### SSL Certificate Issues

**Error:** `SSL handshake failed`

**Solutions:**
- Check certificate validity: `openssl x509 -in cert.pem -text`
- Verify certificate chain
- Test with `openssl s_client -connect domain.com:443`
- Renew certificates: `certbot renew`

### Static File Problems

**Symptoms:** CSS/JS not loading

**Solutions:**
- Check file permissions
- Verify Nginx alias configuration
- Clear browser cache
- Check file paths

## Getting Help

### Diagnostic Information

When reporting issues, include:

1. **System Information:**
   ```bash
   uname -a
   python --version
   pip list | grep -E "(Flask|SQLAlchemy|psycopg2)"
   ```

2. **Application Logs:**
   ```bash
   tail -n 50 /var/log/communitywatch/app.log
   ```

3. **Database Status:**
   ```sql
   SELECT version();
   SELECT COUNT(*) FROM user;
   SELECT COUNT(*) FROM issue;
   ```

4. **Configuration Check:**
   ```bash
   flask shell -c "from app import app; print(app.config['SECRET_KEY'][:10] + '...')"
   ```

### Support Channels

1. **GitHub Issues:** Bug reports and feature requests
2. **Community Forum:** General discussion (future)
3. **Documentation:** Check this guide and API docs
4. **Logs Analysis:** Review application and system logs

### Emergency Procedures

For critical issues:

1. **Stop the Application:** `sudo supervisorctl stop communitywatch`
2. **Check System Resources:** `df -h`, `free -h`, `top`
3. **Review Recent Changes:** Check git log and deployments
4. **Restore from Backup:** If data corruption suspected
5. **Contact Administrators:** Escalate to system administrators

### Prevention

- **Regular Backups:** Daily automated backups
- **Monitoring:** Set up alerts for key metrics
- **Updates:** Keep dependencies and system updated
- **Testing:** Test changes in staging environment
- **Documentation:** Keep runbooks updated

This troubleshooting guide should resolve most common issues. For persistent problems, gather diagnostic information and create detailed GitHub issues.