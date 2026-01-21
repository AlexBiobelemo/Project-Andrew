# Security Guide

This document outlines the security measures, best practices, and considerations for the CommunityWatch platform.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Data Protection](#data-protection)
4. [Input Validation & Sanitization](#input-validation--sanitization)
5. [Rate Limiting & Abuse Prevention](#rate-limiting--abuse-prevention)
6. [Secure Communications](#secure-communications)
7. [File Upload Security](#file-upload-security)
8. [Session Management](#session-management)
9. [CSRF Protection](#csrf-protection)
10. [Security Monitoring](#security-monitoring)
11. [Incident Response](#incident-response)
12. [Compliance Considerations](#compliance-considerations)

## Security Overview

CommunityWatch implements multiple layers of security to protect user data and prevent abuse:

- **Defense in Depth**: Multiple security controls at different layers
- **Privacy by Design**: Security considerations built into architecture
- **Zero Trust**: No implicit trust, continuous verification
- **Least Privilege**: Minimal permissions for all operations

## Authentication & Authorization

### User Authentication

#### Password Security

- **Minimum Requirements**: 8+ characters, uppercase, lowercase, digit, special character
- **Hashing**: Werkzeug PBKDF2 with salt
- **No Plaintext Storage**: Passwords never stored in readable form

#### Two-Factor Authentication (2FA)

- **Required for Moderators**: Users with moderator role and 100+ reputation points
- **TOTP Standard**: RFC 6238 compliant
- **Encrypted Secrets**: 2FA secrets encrypted in database
- **Backup Codes**: Future feature for account recovery

#### OAuth Integration

- **Supported Providers**: Google, Facebook
- **Secure Token Handling**: Tokens validated server-side
- **Account Linking**: OAuth accounts can be linked to existing accounts

### Authorization

#### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| User | Report issues, upvote, comment, view public data |
| Moderator | All user permissions + update issue status, access analytics |
| Admin | All moderator permissions + user management, system config |

#### Permission Checks

```python
@login_required
def update_status(issue_id):
    if not current_user.is_moderator:
        flash('Permission denied.', 'danger')
        return redirect(url_for('main.index'))
    # Proceed with status update
```

## Data Protection

### Encryption at Rest

#### Database Encryption

Sensitive fields are encrypted using AES encryption:

- **User Emails**: `_encrypted_email` field
- **Issue Descriptions**: `_encrypted_description` field
- **Issue Locations**: `_encrypted_location_text` field
- **Comments**: `_encrypted_body` field
- **2FA Secrets**: `_encrypted_twofa_secret` field

#### Encryption Implementation

```python
from app.encryption import encrypt_data, decrypt_data

# Encrypt sensitive data
user._encrypted_email = encrypt_data(email)

# Decrypt when needed
email = decrypt_data(user._encrypted_email)
```

#### Key Management

- **Encryption Keys**: Stored securely (environment variables in production)
- **Key Rotation**: Manual process for security
- **Backup Security**: Encrypted backups with separate keys

### File Encryption

#### Uploaded Images

- **Server-Side Encryption**: Images encrypted before storage
- **Access Control**: Files served through controlled endpoints
- **Secure Filenames**: Werkzeug secure filename generation

### Data Minimization

- **GDPR Compliance**: Only collect necessary data
- **Consent Management**: Explicit consent for data processing
- **Data Retention**: Configurable retention policies
- **Right to Deletion**: Account deletion removes all associated data

## Input Validation & Sanitization

### Input Validation

#### Schema-Based Validation

Using Marshmallow schemas for comprehensive validation:

```python
class IssueReportSchema(Schema):
    description = fields.Str(required=True, validate=[
        fields.validate.Length(min=10, max=500),
        fields.validate.Regexp(r'^[a-zA-Z0-9\s.,!?-]+$')
    ])
    lat = fields.Float(required=True, validate=fields.validate.Range(min=-90, max=90))
    lng = fields.Float(required=True, validate=fields.validate.Range(min=-180, max=180))
```

#### SQL Injection Prevention

- **Parameterized Queries**: SQLAlchemy prevents injection
- **Input Sanitization**: All inputs validated before database operations

### Content Sanitization

#### HTML Sanitization

Using Bleach library for user-generated content:

```python
allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
allowed_attributes = {}
cleaned_content = bleach.clean(user_input, tags=allowed_tags, attributes=allowed_attributes)
```

#### XSS Prevention

- **Template Escaping**: Jinja2 auto-escapes HTML
- **Content Security Policy**: Headers prevent XSS attacks
- **Input Filtering**: Malicious scripts filtered out

### AI-Powered Content Moderation

- **Automated Checking**: AI analyzes text and images for inappropriate content
- **Severity Scoring**: Content flagged based on violation severity
- **Human Oversight**: Moderators can review flagged content

## Rate Limiting & Abuse Prevention

### Rate Limiting Implementation

#### Flask-Limiter Integration

```python
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

@bp.route('/report-issue', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def report_issue():
    # Issue reporting logic
```

#### Dynamic Rate Limiting

User behavior influences rate limits:

```python
def dynamic_limiter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        limits = get_dynamic_limits(request.endpoint)
        limiter.limit(limits)(f)
        return f(*args, **kwargs)
    return decorated_function
```

### Abuse Detection

#### Behavior Tracking

System tracks user behavior patterns:

- **Request Frequency**: Monitor for unusual activity spikes
- **Endpoint Usage**: Track which endpoints are accessed
- **Suspicious Scoring**: Calculate risk scores based on behavior
- **Automated Blocking**: High-risk users temporarily restricted

#### Suspicious Activity Detection

```python
def calculate_suspicious_score(endpoint, method, status_code, user_agent):
    score = 0
    if status_code == 429:  # Rate limited
        score += 20
    if 'bot' in user_agent.lower():
        score += 30
    # Additional checks...
    return score
```

## Secure Communications

### HTTPS Enforcement

#### Production Configuration

```python
class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
```

#### HSTS Headers

Future implementation for HTTP Strict Transport Security.

### API Security

#### Token-Based Access

- **CSRF Tokens**: All forms protected with CSRF tokens
- **API Keys**: Future feature for programmatic access
- **Request Signing**: Optional request signing for high-security endpoints

## File Upload Security

### Upload Validation

#### File Type Checking

```python
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
```

#### Size Limits

```python
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit
```

#### Content Analysis

- **Image Processing**: PIL library validates image integrity
- **Virus Scanning**: Future feature for malware detection
- **Metadata Stripping**: EXIF data removed for privacy

### Secure Storage

- **Encrypted Files**: All uploads encrypted on disk
- **Access Control**: Files served through authenticated endpoints
- **Temporary URLs**: Future feature for secure sharing

## Session Management

### Secure Session Configuration

```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # In production
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = timedelta(days=7)
```

### Session Security

- **HttpOnly Cookies**: Prevent JavaScript access
- **Secure Cookies**: HTTPS-only in production
- **SameSite Protection**: CSRF protection for cross-site requests
- **Session Timeout**: Automatic logout after inactivity

## CSRF Protection

### Flask-WTF CSRF

All forms automatically protected:

```html
<form method="post">
    {{ form.csrf_token }}
    <!-- form fields -->
</form>
```

### AJAX CSRF Protection

```javascript
// Include CSRF token in AJAX requests
headers: {
    'X-CSRFToken': csrfToken
}
```

## Security Monitoring

### Logging

#### Security Event Logging

```python
app.logger.warning(f"Rate limit exceeded: {e.description}")
app.logger.info(f"Moderator {current_user.username} changed issue status")
```

#### Audit Trail

- **User Actions**: Login, logout, password changes
- **Moderation Actions**: Status changes, content moderation
- **Administrative Actions**: Role changes, configuration updates

### Monitoring Tools

#### Application Monitoring

- **Error Tracking**: Sentry integration (future)
- **Performance Monitoring**: Response times and error rates
- **User Behavior**: Anomaly detection

#### Infrastructure Monitoring

- **Server Logs**: System access and error logs
- **Database Monitoring**: Query performance and access patterns
- **Network Monitoring**: Unusual traffic patterns

## Incident Response

### Security Incident Procedure

1. **Detection**: Monitor alerts and logs for anomalies
2. **Assessment**: Evaluate impact and scope of incident
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore systems and data
6. **Lessons Learned**: Document and improve procedures

### Data Breach Response

1. **Immediate Actions**:
   - Notify affected users
   - Reset compromised credentials
   - Monitor for further unauthorized access

2. **Legal Requirements**:
   - Report to relevant authorities if required
   - Document incident details
   - Implement preventive measures

### Communication Plan

- **Internal Communication**: Notify security team and administrators
- **User Communication**: Transparent breach notifications
- **Public Relations**: Coordinate public statements if necessary

## Compliance Considerations

### GDPR Compliance

#### Data Protection Principles

- **Lawfulness, Fairness, Transparency**: Clear privacy policy and consent
- **Purpose Limitation**: Data used only for stated purposes
- **Data Minimization**: Collect only necessary information
- **Accuracy**: Data kept up to date
- **Storage Limitation**: Data retained only as long as necessary
- **Integrity and Confidentiality**: Data protected against unauthorized access
- **Accountability**: Demonstrate compliance

#### User Rights

- **Right to Access**: Users can export their data
- **Right to Rectification**: Users can update their information
- **Right to Erasure**: Account deletion removes all data
- **Right to Data Portability**: Data export in machine-readable format

### Security Best Practices

#### Development Security

- **Secure Coding**: Input validation, output encoding
- **Dependency Management**: Regular security updates
- **Code Reviews**: Security-focused code reviews
- **Testing**: Security testing and vulnerability scanning

#### Operational Security

- **Access Control**: Least privilege access
- **Regular Updates**: Keep systems and dependencies updated
- **Backup Security**: Encrypted, tested backups
- **Monitoring**: Continuous security monitoring

#### Incident Prevention

- **Security Training**: Regular security awareness training
- **Vulnerability Management**: Regular security assessments
- **Change Management**: Controlled deployment process
- **Business Continuity**: Disaster recovery planning

### Security Checklist

#### Pre-Deployment

- [ ] Environment variables configured securely
- [ ] Database credentials encrypted
- [ ] HTTPS certificates installed
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Monitoring and logging active

#### Regular Maintenance

- [ ] Security updates applied
- [ ] Logs reviewed regularly
- [ ] Access permissions audited
- [ ] Backups tested
- [ ] Security assessments performed

#### Incident Response

- [ ] Incident response plan documented
- [ ] Contact information current
- [ ] Communication templates ready
- [ ] Recovery procedures tested

This security guide should be reviewed regularly and updated as new threats emerge or features are added to the platform.