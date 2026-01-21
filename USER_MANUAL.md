# User Manual: Moderators and Administrators

This manual provides comprehensive guidance for moderators and administrators of the CommunityWatch platform.

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Roles and Permissions](#user-roles-and-permissions)
3. [Moderation Tools](#moderation-tools)
4. [Issue Management](#issue-management)
5. [User Management](#user-management)
6. [Analytics and Reporting](#analytics-and-reporting)
7. [Gamification System](#gamification-system)
8. [Security Features](#security-features)
9. [Maintenance Tasks](#maintenance-tasks)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing the Platform

1. Navigate to the CommunityWatch homepage
2. Click "Login" and enter your moderator/administrator credentials
3. If 2FA is enabled, complete the two-factor authentication

### Dashboard Overview

After logging in, you'll see:
- **Main Map**: Interactive map showing all reported issues
- **Analytics Dashboard**: Community statistics and trends
- **Navigation Menu**: Access to moderation tools and user management

## User Roles and Permissions

### Role Hierarchy

1. **User**: Basic community member
   - Report issues
   - Upvote issues
   - Comment on issues
   - View public profiles

2. **Moderator**: Community moderator
   - All user permissions
   - Update issue status
   - Access analytics dashboard
   - Moderate content (future feature)

3. **Administrator**: Platform administrator
   - All moderator permissions
   - User role management
   - System configuration
   - Access to administrative tools

### Checking User Roles

To check a user's role:
1. Visit their profile page: `/user/{username}`
2. Role information is displayed on their profile
3. Administrators can change roles via the Flask shell

## Moderation Tools

### Issue Status Management

#### Updating Issue Status

1. Navigate to the issue details page: `/issue/{issue_id}`
2. Click the "Update Status" button (moderators only)
3. Select new status from dropdown:
   - **Reported**: Initial status (default)
   - **In Progress**: Work has begun
   - **Resolved**: Issue has been fixed
4. Add optional notes about the resolution
5. Click "Update Status"

#### Status Change Notifications

When you update an issue status:
- The reporter receives a notification
- All users who upvoted the issue are notified
- Notifications appear in real-time if users are online

### Content Moderation

#### Automated Moderation

CommunityWatch uses AI to automatically moderate content:
- **Text Analysis**: Checks for inappropriate language
- **Image Analysis**: Scans uploaded photos for violations
- **Duplicate Detection**: Identifies similar issues

#### Manual Review (Future Feature)

For manual content review:
1. Access the moderation queue (future feature)
2. Review flagged content
3. Approve or remove inappropriate content

## Issue Management

### Viewing Issues

#### Map View
- Issues are displayed as markers on the interactive map
- Color coding indicates status:
  - Red: Reported
  - Yellow: In Progress
  - Green: Resolved
- Click markers to view issue details

#### List View
- Access detailed issue lists via API endpoints
- Filter by status, category, or location
- Sort by date, upvotes, or priority

### Issue Categories

CommunityWatch supports these issue categories:
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

### Priority Scoring

Issues are automatically prioritized based on:
- Number of upvotes
- Issue category severity
- Time since reporting
- Geographic clustering

## User Management

### Viewing User Profiles

1. Click on any username to view their profile
2. Profile shows:
   - Username and join date
   - Reputation points
   - Issues reported
   - Badges earned
   - Recent activity

### Managing User Roles

**Promoting to Moderator (Administrators Only):**

```bash
flask shell
```

```python
from app.models import User
user = User.query.filter_by(username='username_here').first()
if user:
    user.role = 'moderator'
    db.session.commit()
    print(f"User {user.username} is now a moderator")
```

**Demoting Users:**

```python
user.role = 'user'
db.session.commit()
```

### User Activity Monitoring

#### Reputation System

Users earn reputation points for:
- Reporting issues: +5 points
- Receiving upvotes on issues: +2 points per upvote
- Having issues resolved: +20 points

#### Behavior Tracking

The system tracks user behavior for security:
- Request patterns
- Rate limiting violations
- Suspicious activity scores

### Handling Problem Users

1. **Rate Limiting Violations**: Automatic rate limiting handles abuse
2. **Inappropriate Content**: Use moderation tools to remove content
3. **Spam Reports**: Monitor for patterns and take appropriate action
4. **Account Suspension**: Contact platform administrators for severe cases

## Analytics and Reporting

### Community Analytics Dashboard

Access at `/analytics` (login required)

#### Available Metrics

- **Issue Status Breakdown**: Pie chart of issue statuses
- **Top Voted Issues**: Most upvoted unresolved issues
- **Heatmap**: Geographic distribution of issues
- **Trend Analysis**: Issue reporting over time

#### Exporting Data

1. Visit user profile: `/user/{username}`
2. Click "Export Data" button
3. Download JSON file containing:
   - User profile information
   - Reported issues
   - Comments and upvotes
   - Notification history
   - Badge and challenge progress

### Weekly Reports

#### AI-Generated Reports

1. POST to `/generate-report` endpoint
2. Generates summary including:
   - Total issues reported
   - Category breakdown
   - Most upvoted issues
   - Community trends

#### Manual Reporting

Use database queries for custom reports:

```sql
-- Issues by status
SELECT status, COUNT(*) FROM issue GROUP BY status;

-- Top reporters
SELECT reporter_id, COUNT(*) as issues_reported
FROM issue
GROUP BY reporter_id
ORDER BY issues_reported DESC
LIMIT 10;

-- Recent activity
SELECT * FROM issue
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

## Gamification System

### Badges

Users can earn badges for achievements:
- **First Report**: Report your first issue
- **Community Helper**: Receive 10 upvotes
- **Issue Resolver**: Have an issue resolved
- **Top Contributor**: Report 50+ issues

### Challenges

Ongoing challenges encourage participation:
- Report issues in different categories
- Maintain upvote streaks
- Help resolve community issues

### Managing Gamification

#### Adding New Badges

```python
from app.models import Badge
from app import db

badge = Badge(
    name="New Badge",
    description="Description of achievement",
    criteria="Criteria for earning",
    icon="badge_icon.png"
)
db.session.add(badge)
db.session.commit()
```

#### Updating Challenges

```python
from app.models import Challenge

challenge = Challenge.query.filter_by(name="Challenge Name").first()
challenge.reward_points = 25
db.session.commit()
```

## Security Features

### Two-Factor Authentication

#### For Moderators

Moderators with 100+ reputation points must enable 2FA:
1. Go to profile page
2. Click "Setup 2FA"
3. Scan QR code with authenticator app
4. Enter verification code

#### Managing 2FA

Administrators can reset 2FA for users if needed:

```python
user.twofa_enabled = False
user.twofa_secret = None
db.session.commit()
```

### Rate Limiting

#### Default Limits

- General: 200 requests/day, 50/hour
- Issue reporting: 10/minute
- Upvoting: 20/minute
- API calls: Vary by endpoint

#### Monitoring Rate Limits

Check rate limiting logs in Flask logs or database:

```sql
SELECT * FROM user_behavior
WHERE suspicious_score > 50
ORDER BY timestamp DESC;
```

### Data Encryption

Sensitive data is encrypted:
- User emails
- Issue descriptions and locations
- 2FA secrets
- Uploaded files

### Security Best Practices

1. **Use Strong Passwords**: Enforce password requirements
2. **Enable 2FA**: Required for moderators
3. **Monitor Logs**: Regularly check for suspicious activity
4. **Secure Sessions**: Use HTTPS in production
5. **Regular Backups**: Backup encrypted data securely

## Maintenance Tasks

### Database Maintenance

#### Regular Cleanup

Run scheduled tasks for maintenance:

```python
# In Flask shell
from app.tasks import delete_old_issues, update_priorities

delete_old_issues()
update_priorities()
```

#### Database Backups

```bash
# PostgreSQL backup
pg_dump -U communitywatch_user -h localhost communitywatch > backup.sql

# SQLite backup
cp app.db app.db.backup
```

#### Index Optimization

Monitor and optimize database indexes:

```sql
-- Check index usage
SELECT * FROM pg_stat_user_indexes;

-- Reindex if needed
REINDEX INDEX CONCURRENTLY index_name;
```

### Cache Management

#### Clearing Analytics Cache

```python
from app.cache import cache
cache.delete('analytics_data')
cache.delete('community_stats')
```

#### Redis Maintenance

```bash
# Check Redis memory usage
redis-cli info memory

# Clear all cache
redis-cli FLUSHALL
```

### AI Service Management

#### Updating Embeddings

Regenerate search embeddings for existing issues:

```python
from app.models import Issue
from app.ai_services import generate_embedding

issues = Issue.query.filter(Issue.embedding == None).all()
for issue in issues:
    text = f"{issue.category}: {issue.description}"
    issue.embedding = generate_embedding(text)
db.session.commit()
```

#### Monitoring API Usage

Check AI service usage and costs:
- Monitor Gemini API dashboard
- Set up budget alerts
- Optimize prompt sizes

## Troubleshooting

### Common Issues

#### Users Can't Login

1. Check if account exists
2. Verify password is correct
3. Check if 2FA is required
4. Reset password if needed

#### Issues Not Appearing on Map

1. Verify coordinates are valid
2. Check if issue was saved to database
3. Clear analytics cache
4. Check for JavaScript errors

#### Slow Performance

1. Check database query performance
2. Clear caches
3. Optimize indexes
4. Check server resources

#### AI Features Not Working

1. Verify GEMINI_API_KEY is set
2. Check API quota
3. Review error logs
4. Test API connectivity

### Emergency Procedures

#### System Down

1. Check server status
2. Review error logs
3. Restart services
4. Contact technical support

#### Security Incident

1. Isolate affected systems
2. Change all passwords
3. Review access logs
4. Report incident if necessary

#### Data Loss

1. Restore from backup
2. Verify data integrity
3. Update affected users
4. Implement prevention measures

### Support Resources

- **Technical Documentation**: See DEVELOPER_SETUP.md
- **API Documentation**: See API_DOCUMENTATION.md
- **Configuration Guide**: See CONFIGURATION.md
- **GitHub Issues**: Report bugs and request features

### Contact Information

For technical support or questions:
- Create GitHub issue
- Contact platform administrators
- Check community forums (future feature)

## Best Practices

### Moderation Guidelines

1. **Be Fair and Consistent**: Apply rules equally to all users
2. **Communicate Clearly**: Explain decisions when updating issues
3. **Protect Privacy**: Don't share personal information
4. **Encourage Positive Behavior**: Recognize good contributions

### Community Management

1. **Monitor Trends**: Use analytics to identify problem areas
2. **Engage Users**: Respond to comments and questions
3. **Promote Quality**: Encourage detailed, accurate reports
4. **Resolve Issues**: Work with authorities to fix problems

### Platform Maintenance

1. **Regular Backups**: Daily automated backups
2. **Monitor Performance**: Set up alerts for issues
3. **Update Dependencies**: Keep packages current
4. **Security Audits**: Regular security reviews

### Personal Development

1. **Stay Informed**: Follow platform updates
2. **Learn Tools**: Master moderation features
3. **Build Relationships**: Connect with other moderators
4. **Provide Feedback**: Suggest improvements

Remember: As a moderator or administrator, you represent the platform and set the tone for community interaction. Lead by example and foster a positive, productive environment for issue reporting and resolution.