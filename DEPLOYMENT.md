# Deployment Guide

This guide covers deploying CommunityWatch to production environments, including cloud platforms, traditional servers, and containerized deployments.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Application Deployment](#application-deployment)
5. [Database Setup](#database-setup)
6. [Web Server Configuration](#web-server-configuration)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Scaling Considerations](#scaling-considerations)
11. [Cloud Deployments](#cloud-deployments)
12. [Container Deployment](#container-deployment)
13. [Troubleshooting](#troubleshooting)

## Deployment Overview

CommunityWatch can be deployed using several strategies:

- **Traditional Server**: VPS or dedicated server with Nginx + Gunicorn
- **Cloud Platforms**: AWS, Google Cloud, Azure, Heroku
- **Containerized**: Docker containers with orchestration
- **Serverless**: AWS Lambda, Google Cloud Functions (future)

### Architecture

```
Internet -> Load Balancer -> Web Server -> WSGI Server -> Flask App -> Database
                                      -> Redis Cache
                                      -> Background Tasks
```

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+, CentOS 8+, or similar Linux distribution
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Storage**: 20GB+ for application, database, and uploads
- **Network**: Stable internet connection

### Software Requirements

- **Python**: 3.8 or higher
- **PostgreSQL**: 12 or higher
- **Redis**: 6.0+ (optional, for caching)
- **Nginx**: Latest stable version
- **Supervisor**: For process management

## Environment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3 python3-pip python3-venv postgresql redis-server nginx supervisor git

# Install certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

### 2. User and Directory Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash communitywatch

# Create application directory
sudo mkdir -p /var/www/communitywatch
sudo chown communitywatch:communitywatch /var/www/communitywatch

# Create logs directory
sudo mkdir -p /var/log/communitywatch
sudo chown communitywatch:communitywatch /var/log/communitywatch
```

### 3. Python Environment

```bash
# Switch to application user
sudo -u communitywatch bash

# Set up virtual environment
cd /var/www/communitywatch
python3 -m venv venv
source venv/bin/activate

# Clone repository
git clone https://github.com/AlexBiobelemo/Project-Andrew-CommunityWatch-/tree/main/Version%202 .
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

## Application Deployment

### 1. Configuration

Create production configuration:

```bash
# .env file
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@localhost/communitywatch
GEMINI_API_KEY=your-production-gemini-key
UPLOAD_FOLDER=/var/www/communitywatch/uploads
REDIS_URL=redis://localhost:6379/0
```

### 2. Database Setup

```bash
# Create database user and database
sudo -u postgres psql

CREATE USER communitywatch_prod WITH ENCRYPTED PASSWORD 'strong_password';
CREATE DATABASE communitywatch_prod OWNER communitywatch_prod;
GRANT ALL PRIVILEGES ON DATABASE communitywatch_prod TO communitywatch_prod;
\q

# Run migrations
cd /var/www/communitywatch
source venv/bin/activate
flask db upgrade

# Initialize gamification
flask shell -c "from app.utils import initialize_gamification; initialize_gamification()"
```

### 3. Static Files

```bash
# Collect static files (if any)
mkdir -p static
# Copy static assets to static directory
```

### 4. Gunicorn Configuration

Create `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "communitywatch"
group = "communitywatch"
tmp_upload_dir = None
```

## Web Server Configuration

### Nginx Configuration

Create `/etc/nginx/sites-available/communitywatch`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static {
        alias /var/www/communitywatch/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploaded files (encrypted, served through app)
    location /uploads {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/communitywatch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL/TLS Configuration

### Let's Encrypt SSL

```bash
# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

### Manual SSL Configuration

If using custom SSL certificates:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Process Management

### Supervisor Configuration

Create `/etc/supervisor/conf.d/communitywatch.conf`:

```ini
[program:communitywatch]
command=/var/www/communitywatch/venv/bin/gunicorn -c gunicorn.conf.py run:app
directory=/var/www/communitywatch
user=communitywatch
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/communitywatch/gunicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=3
```

Update supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start communitywatch
```

### Background Tasks

For scheduled tasks, configure additional supervisor programs:

```ini
[program:communitywatch-scheduler]
command=/var/www/communitywatch/venv/bin/python run_scheduler.py
directory=/var/www/communitywatch
user=communitywatch
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/communitywatch/scheduler.log
```

## Monitoring and Logging

### Application Logging

Configure logging in production:

```python
# config.py
class ProductionConfig(Config):
    LOG_LEVEL = logging.INFO
    LOG_FILE = '/var/log/communitywatch/app.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 5
```

### System Monitoring

#### Install monitoring tools:

```bash
# Prometheus Node Exporter
sudo apt install -y prometheus-node-exporter

# Grafana (optional)
sudo apt install -y grafana

# Log aggregation
sudo apt install -y rsyslog
```

#### Health Check Endpoint

Add to `routes.py`:

```python
@bp.route('/health')
def health_check():
    # Check database connectivity
    try:
        db.session.execute(text('SELECT 1'))
        db_status = 'ok'
    except Exception:
        db_status = 'error'

    # Check Redis if configured
    redis_status = 'ok'
    if current_app.config.get('REDIS_URL'):
        try:
            from app.cache import cache
            cache.get('health_check')
        except Exception:
            redis_status = 'error'

    return jsonify({
        'status': 'ok' if db_status == 'ok' and redis_status == 'ok' else 'error',
        'database': db_status,
        'redis': redis_status,
        'timestamp': datetime.utcnow().isoformat()
    })
```

### Log Rotation

Configure logrotate for application logs:

```bash
# /etc/logrotate.d/communitywatch
/var/log/communitywatch/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 communitywatch communitywatch
    postrotate
        supervisorctl restart communitywatch
    endscript
}
```

## Backup and Recovery

### Database Backup

#### Automated PostgreSQL Backup

Create `/usr/local/bin/backup-communitywatch.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/communitywatch"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/communitywatch_$DATE.sql"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U communitywatch_prod -h localhost communitywatch_prod > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Optional: Upload to cloud storage
# aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/backup-communitywatch.sh
sudo crontab -e

# Add: 0 2 * * * /usr/local/bin/backup-communitywatch.sh
```

### File Backup

#### Upload Directory Backup

```bash
# Add to backup script
UPLOAD_BACKUP="$BACKUP_DIR/uploads_$DATE.tar.gz"
tar -czf $UPLOAD_BACKUP -C /var/www/communitywatch/uploads .
```

### Recovery Procedure

1. **Stop Application**:
   ```bash
   sudo supervisorctl stop communitywatch
   ```

2. **Restore Database**:
   ```bash
   gunzip communitywatch_backup.sql.gz
   psql -U communitywatch_prod -d communitywatch_prod < communitywatch_backup.sql
   ```

3. **Restore Files**:
   ```bash
   tar -xzf uploads_backup.tar.gz -C /var/www/communitywatch/uploads
   ```

4. **Restart Application**:
   ```bash
   sudo supervisorctl start communitywatch
   ```

## Scaling Considerations

### Horizontal Scaling

#### Load Balancer Configuration

```nginx
upstream communitywatch_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://communitywatch_app;
        # ... other proxy settings
    }
}
```

#### Database Scaling

- Use read replicas for analytics queries
- Implement database connection pooling
- Consider database sharding for large deployments

#### Redis Clustering

For high availability Redis setup:

```bash
# Install Redis cluster
redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003
```

### Performance Optimization

#### Gunicorn Tuning

```python
# gunicorn.conf.py for high traffic
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000
```

#### Database Optimization

```sql
-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_issue_status_timestamp ON issue(status, timestamp);
CREATE INDEX CONCURRENTLY idx_issue_location ON issue USING gist (point(latitude, longitude));

-- Analyze tables
ANALYZE issue;
ANALYZE user;
```

## Cloud Deployments

### AWS Deployment

#### EC2 Setup

1. Launch EC2 instance (t3.medium or larger)
2. Configure security groups (ports 22, 80, 443)
3. Attach EBS volume for data
4. Follow traditional server setup above

#### RDS PostgreSQL

```bash
# Use RDS endpoint in DATABASE_URL
DATABASE_URL=postgresql://user:password@your-rds-endpoint.amazonaws.com/communitywatch
```

#### S3 for File Storage

```python
# config.py
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = 'your-communitywatch-bucket'

# Use boto3 for S3 uploads
```

### Heroku Deployment

#### Procfile

```
web: gunicorn run:app
worker: python run_scheduler.py
```

#### Heroku Postgres

```bash
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set FLASK_ENV=production
```

#### Heroku Redis (optional)

```bash
heroku addons:create heroku-redis:hobby-dev
```

## Container Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db/communitywatch
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - uploads:/app/uploads

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=communitywatch
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
  uploads:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: communitywatch
spec:
  replicas: 3
  selector:
    matchLabels:
      app: communitywatch
  template:
    metadata:
      labels:
        app: communitywatch
    spec:
      containers:
      - name: communitywatch
        image: your-registry/communitywatch:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: database-url
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Troubleshooting

### Common Deployment Issues

#### Application Won't Start

1. **Check Logs**:
   ```bash
   sudo supervisorctl status communitywatch
   sudo tail -f /var/log/communitywatch/gunicorn.log
   ```

2. **Environment Variables**:
   ```bash
   sudo -u communitywatch bash -c 'cd /var/www/communitywatch && source venv/bin/activate && python -c "import os; print(os.environ.get(\"SECRET_KEY\"))"'
   ```

3. **Database Connection**:
   ```bash
   sudo -u communitywatch psql -U communitywatch_prod -d communitywatch_prod -c "SELECT 1"
   ```

#### High Memory Usage

1. **Check Gunicorn Workers**:
   ```python
   # Reduce workers in gunicorn.conf.py
   workers = 2
   ```

2. **Enable Connection Pooling**:
   ```python
   # config.py
   SQLALCHEMY_POOL_SIZE = 10
   SQLALCHEMY_MAX_OVERFLOW = 20
   ```

#### Slow Response Times

1. **Database Query Optimization**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM issue WHERE status = 'Reported';
   ```

2. **Enable Caching**:
   ```python
   CACHE_TYPE = 'redis'
   CACHE_REDIS_URL = 'redis://localhost:6379/0'
   ```

#### SSL Issues

1. **Certificate Validation**:
   ```bash
   openssl s_client -connect your-domain.com:443 -servername your-domain.com
   ```

2. **Renewal Issues**:
   ```bash
   sudo certbot certificates
   sudo certbot renew
   ```

### Monitoring Commands

```bash
# Check application status
sudo supervisorctl status

# Check nginx status
sudo systemctl status nginx

# Check database connections
psql -U communitywatch_prod -d communitywatch_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Check disk usage
df -h

# Check memory usage
free -h

# Check application logs
tail -f /var/log/communitywatch/app.log
```

### Performance Tuning

#### Nginx Optimization

```nginx
worker_processes auto;
worker_connections 1024;

# Enable gzip
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss;

# Cache static files
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### Database Tuning

```postgresql
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

This deployment guide provides a comprehensive foundation for production deployment. Adjust configurations based on your specific requirements and scale.