# CommunityWatch Database Schema

## Overview

CommunityWatch uses PostgreSQL as its primary database with SQLAlchemy ORM for data management. The schema includes encryption for sensitive data and supports gamification features.

## Tables

### User Table

Stores user account information and authentication data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique user identifier |
| username | VARCHAR(64) | UNIQUE, NOT NULL | User's display name |
| _encrypted_email | VARCHAR(256) | UNIQUE, NOT NULL | Encrypted email address |
| password_hash | VARCHAR(256) | NULL | Hashed password (NULL for OAuth users) |
| reputation_points | INTEGER | DEFAULT 0 | User's reputation score |
| role | VARCHAR(20) | DEFAULT 'user', NOT NULL | User role (user, moderator, admin) |
| oauth_provider | VARCHAR(20) | NULL | OAuth provider (google, facebook) |
| oauth_id | VARCHAR(100) | NULL | OAuth provider's user ID |
| _encrypted_twofa_secret | VARCHAR(256) | NULL | Encrypted 2FA secret |
| twofa_enabled | BOOLEAN | DEFAULT FALSE | Whether 2FA is enabled |
| data_processing_consent | BOOLEAN | DEFAULT FALSE | GDPR data processing consent |
| marketing_consent | BOOLEAN | DEFAULT FALSE | Marketing communications consent |
| consent_date | DATETIME | NULL | When consent was given |
| last_upvote_time | DATETIME | NULL | Timestamp of last upvote |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Account creation time |

**Indexes:**
- username
- _encrypted_email
- reputation_points
- role

**Relationships:**
- One-to-many with Issue (reporter)
- One-to-many with Upvote (voter)
- One-to-many with Comment (author)
- One-to-many with Notification (user)
- One-to-many with UserBadge (user)
- One-to-many with UserChallenge (user)
- One-to-many with Geofence (user)
- One-to-many with UserBehavior (user)

### Issue Table

Stores reported community issues.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique issue identifier |
| category | VARCHAR(64) | NOT NULL | Issue category |
| _encrypted_description | TEXT | NOT NULL | Encrypted issue description |
| latitude | FLOAT | NOT NULL | Issue latitude |
| longitude | FLOAT | NOT NULL | Issue longitude |
| _encrypted_location_text | VARCHAR(256) | NULL | Encrypted location description |
| image_filename | VARCHAR(200) | NULL | Uploaded image filename |
| timestamp | DATETIME | DEFAULT CURRENT_TIMESTAMP, NOT NULL | When issue was reported |
| status | VARCHAR(64) | DEFAULT 'Reported', NOT NULL | Issue status |
| resolved_at | DATETIME | NULL | When issue was resolved |
| upvote_count | INTEGER | DEFAULT 0 | Number of upvotes |
| priority_score | FLOAT | DEFAULT 0.0 | Calculated priority score |
| embedding | PICKLE | NULL | AI-generated text embedding |
| geojson | JSON | NULL | GeoJSON geometry data |
| reporter_id | INTEGER | FOREIGN KEY(user.id), NOT NULL | Reporting user |

**Indexes:**
- category
- latitude, longitude
- status
- upvote_count
- priority_score
- reporter_id
- timestamp

**Relationships:**
- Many-to-one with User (reporter)
- One-to-many with Comment (issue)
- One-to-many with Upvote (issue)

**Valid Categories:**
- Blocked Drainage
- Broken Park Bench
- Broken Streetlight
- Broken Traffic Light
- Damaged Public Property
- Faded Road Markings
- Fallen Tree
- Flooding
- Graffiti
- Leaking Pipe
- Overgrown Vegetation
- Pothole
- Power Line Down
- Stray Animal Concern
- Waste Dumping
- Other

### Comment Table

Stores user comments on issues.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique comment identifier |
| _encrypted_body | TEXT | NOT NULL | Encrypted comment text |
| timestamp | DATETIME | INDEX, DEFAULT CURRENT_TIMESTAMP, NOT NULL | When comment was posted |
| issue_id | INTEGER | FOREIGN KEY(issue.id), INDEX, NOT NULL | Associated issue |
| author_id | INTEGER | FOREIGN KEY(user.id), INDEX, NOT NULL | Commenting user |

**Indexes:**
- timestamp
- issue_id
- author_id

**Relationships:**
- Many-to-one with Issue (issue)
- Many-to-one with User (author)

### Upvote Table

Tracks user upvotes on issues.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique upvote identifier |
| voter_id | INTEGER | FOREIGN KEY(user.id), INDEX, NOT NULL | User who upvoted |
| issue_id | INTEGER | FOREIGN KEY(issue.id), INDEX, NOT NULL | Upvoted issue |

**Indexes:**
- voter_id
- issue_id

**Relationships:**
- Many-to-one with User (voter)
- Many-to-one with Issue (issue)

### Notification Table

Stores user notifications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique notification identifier |
| name | VARCHAR(128) | INDEX, NOT NULL | Notification type |
| data | JSON | NOT NULL | Notification data |
| timestamp | FLOAT | INDEX, DEFAULT CURRENT_TIMESTAMP, NOT NULL | When notification was created |
| user_id | INTEGER | FOREIGN KEY(user.id), INDEX, NOT NULL | Target user |

**Indexes:**
- name
- timestamp
- user_id

**Relationships:**
- Many-to-one with User (user)

### Badge Table

Gamification achievement badges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique badge identifier |
| name | VARCHAR(64) | UNIQUE, NOT NULL | Badge name |
| description | TEXT | NOT NULL | Badge description |
| icon | VARCHAR(64) | NULL | Badge icon filename |
| criteria | TEXT | NOT NULL | Achievement criteria |

### UserBadge Table

Associates users with earned badges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique association identifier |
| user_id | INTEGER | FOREIGN KEY(user.id), NOT NULL | User who earned badge |
| badge_id | INTEGER | FOREIGN KEY(badge.id), NOT NULL | Earned badge |
| awarded_at | DATETIME | DEFAULT CURRENT_TIMESTAMP, NOT NULL | When badge was awarded |

**Relationships:**
- Many-to-one with User (user)
- Many-to-one with Badge (badge)

### Challenge Table

Gamification tasks and challenges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique challenge identifier |
| name | VARCHAR(64) | UNIQUE, NOT NULL | Challenge name |
| description | TEXT | NOT NULL | Challenge description |
| criteria | TEXT | NOT NULL | Completion criteria |
| reward_points | INTEGER | DEFAULT 0 | Reputation points reward |
| active | BOOLEAN | DEFAULT TRUE | Whether challenge is active |

### UserChallenge Table

Tracks user progress on challenges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique progress identifier |
| user_id | INTEGER | FOREIGN KEY(user.id), NOT NULL | User attempting challenge |
| challenge_id | INTEGER | FOREIGN KEY(challenge.id), NOT NULL | Target challenge |
| progress | INTEGER | DEFAULT 0 | Current progress |
| completed_at | DATETIME | NULL | When challenge was completed |

**Relationships:**
- Many-to-one with User (user)
- Many-to-one with Challenge (challenge)

### Geofence Table

User-defined geographic notification areas.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique geofence identifier |
| user_id | INTEGER | FOREIGN KEY(user.id), NOT NULL | Geofence owner |
| name | VARCHAR(128) | NOT NULL | Geofence name |
| geometry | JSON | NOT NULL | GeoJSON geometry (Polygon/MultiPolygon) |
| notify_on_issue | BOOLEAN | DEFAULT TRUE | Whether to notify on issues in area |

**Relationships:**
- Many-to-one with User (user)

### UserBehavior Table

Tracks user behavior patterns for rate limiting and security.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique behavior record identifier |
| user_id | INTEGER | FOREIGN KEY(user.id), NULL | Associated user (NULL for anonymous) |
| ip_address | VARCHAR(45) | NOT NULL | Request IP address |
| endpoint | VARCHAR(256) | NOT NULL | Accessed endpoint |
| method | VARCHAR(10) | NOT NULL | HTTP method |
| timestamp | DATETIME | DEFAULT CURRENT_TIMESTAMP, NOT NULL | When request was made |
| status_code | INTEGER | NOT NULL | HTTP response status code |
| user_agent | TEXT | NULL | User agent string |
| suspicious_score | INTEGER | DEFAULT 0 | Suspicious behavior score (0-100) |

**Indexes:**
- user_id
- ip_address
- endpoint
- timestamp

**Relationships:**
- Many-to-one with User (user)

## Data Encryption

Sensitive fields are encrypted using AES encryption:

- User emails (_encrypted_email)
- User 2FA secrets (_encrypted_twofa_secret)
- Issue descriptions (_encrypted_description)
- Issue location text (_encrypted_location_text)
- Comment bodies (_encrypted_body)

Encryption keys are managed through the `app/encryption.py` module.

## Database Migrations

The application uses Flask-Migrate for database schema versioning. Migration files are stored in `migrations/versions/`.

## Performance Considerations

- Indexes are created on frequently queried columns
- Large text fields use appropriate data types
- JSON fields store complex geometric and notification data
- Embedding vectors are stored as pickled objects for AI search functionality

## Backup and Recovery

Regular database backups should include:
- Full schema and data dumps
- Migration history
- Encryption key backups (secure storage required)