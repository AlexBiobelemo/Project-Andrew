"""
API routes for CommunityWatch with versioning support.
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import select
from app import db
from app.cache import cache
from app.models import Issue, User
from app.rate_limiting import dynamic_limiter

# Create versioned API blueprints
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


@api_v1.route('/issues', methods=['GET'])
@login_required
@dynamic_limiter("50 per minute")
def get_issues():
    """
    Get issues with optional filtering.

    Query parameters:
        status: Filter by status (Reported, In Progress, Resolved)
        category: Filter by category
        limit: Maximum number of results (default: 50, max: 100)
        offset: Pagination offset (default: 0)
    """
    # Parse query parameters
    status = request.args.get('status')
    category = request.args.get('category')
    limit = min(int(request.args.get('limit', 50)), 100)
    offset = int(request.args.get('offset', 0))
    
    # Create cache key based on query parameters
    cache_key = f"issues_{status or 'all'}_{category or 'all'}_{limit}_{offset}"
    
    # Try to get cached result
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)

    # Build query
    query = select(Issue).options(db.joinedload(Issue.reporter))

    if status:
        query = query.where(Issue.status == status)
    if category:
        query = query.where(Issue.category == category)

    # Execute query with pagination
    issues = db.session.scalars(query.offset(offset).limit(limit)).all()

    # Format response
    issues_data = []
    for issue in issues:
        issues_data.append({
            'id': issue.id,
            'category': issue.category,
            'description': issue.description,
            'latitude': issue.latitude,
            'longitude': issue.longitude,
            'location_text': issue.location_text,
            'status': issue.status,
            'upvote_count': issue.upvote_count or 0,
            'timestamp': issue.timestamp.isoformat(),
            'reporter': {
                'id': issue.reporter.id,
                'username': issue.reporter.username
            } if issue.reporter else None
        })

    result = {
        'issues': issues_data,
        'total': len(issues_data),
        'limit': limit,
        'offset': offset
    }
    
    # Cache the result for 5 minutes
    cache.set(cache_key, result, timeout=300)

    return jsonify(result)


@api_v1.route('/issues/<int:issue_id>', methods=['GET'])
@login_required
@dynamic_limiter("100 per minute")
def get_issue(issue_id: int):
    """Get a specific issue by ID."""
    issue = db.session.get(Issue, issue_id, options=[db.joinedload(Issue.reporter)])

    if not issue:
        return jsonify({'error': 'Issue not found'}), 404

    issue_data = {
        'id': issue.id,
        'category': issue.category,
        'description': issue.description,
        'latitude': issue.latitude,
        'longitude': issue.longitude,
        'location_text': issue.location_text,
        'status': issue.status,
        'upvote_count': issue.upvote_count or 0,
        'timestamp': issue.timestamp.isoformat(),
        'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
        'reporter': {
            'id': issue.reporter.id,
            'username': issue.reporter.username
        } if issue.reporter else None
    }

    return jsonify(issue_data)


@api_v1.route('/user/profile', methods=['GET'])
@login_required
@dynamic_limiter("30 per minute")
def get_user_profile():
    """Get current user's profile information."""
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'reputation_points': current_user.reputation_points or 0,
        'role': current_user.role,
        'twofa_enabled': current_user.twofa_enabled,
        'is_moderator': current_user.is_moderator,
        'is_admin': current_user.is_admin
    }

    return jsonify(user_data)


@api_v1.route('/stats', methods=['GET'])
@login_required
@dynamic_limiter("20 per minute")
def get_stats():
    """Get community statistics."""
    # Try to get cached stats
    cached_stats = cache.get('community_stats')
    if cached_stats:
        return jsonify(cached_stats)
    
    from sqlalchemy import func

    # Get issue counts by status
    status_counts = dict(db.session.query(Issue.status, func.count(Issue.status)).group_by(Issue.status).all())

    # Get total users
    total_users = db.session.query(func.count(User.id)).scalar()

    # Get total issues
    total_issues = db.session.query(func.count(Issue.id)).scalar()

    stats = {
        'total_users': total_users,
        'total_issues': total_issues,
        'issues_by_status': status_counts,
        'active_users': db.session.query(func.count(User.id)).where(User.reputation_points > 0).scalar()
    }

    # Cache stats for 1 hour
    cache.set('community_stats', stats, timeout=3600)

    return jsonify(stats)


# API v2 blueprint for future versions
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# For now, v2 inherits from v1 but can be extended
@api_v2.route('/issues', methods=['GET'])
@login_required
@dynamic_limiter("50 per minute")
def get_issues_v2():
    """Get issues with enhanced filtering for v2."""
    # Call v1 implementation but add additional features
    response = get_issues()
    if response.status_code != 200:
        return response

    data = response.get_json()

    # Add v2-specific enhancements
    # For example, include priority scores
    for issue in data['issues']:
        issue_id = issue['id']
        db_issue = db.session.get(Issue, issue_id)
        if db_issue:
            issue['priority_score'] = db_issue.priority_score or 0.0

    return jsonify(data)