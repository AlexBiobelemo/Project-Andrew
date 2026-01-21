"""
Sophisticated rate limiting based on user behavior patterns for CommunityWatch.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import request, current_app
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_login import current_user
from sqlalchemy import func, and_, or_
from app import db
from app.models import UserBehavior, User


def user_or_ip_key():
    """Return user ID for authenticated users or IP address for rate limiting."""
    return str(current_user.id) if current_user.is_authenticated else get_remote_address()


def track_user_behavior(status_code: int, suspicious_score: int = 0) -> None:
    """
    Track user behavior for rate limiting analysis.

    Args:
        status_code: HTTP response status code
        suspicious_score: Score indicating suspicious behavior (0-100)
    """
    try:
        behavior = UserBehavior(
            user_id=current_user.id if current_user.is_authenticated else None,
            ip_address=get_remote_address(),
            endpoint=request.endpoint or 'unknown',
            method=request.method,
            status_code=status_code,
            user_agent=request.headers.get('User-Agent'),
            suspicious_score=suspicious_score
        )
        db.session.add(behavior)
        db.session.commit()
    except Exception as e:
        current_app.logger.warning(f"Failed to track user behavior: {e}")
        db.session.rollback()


def calculate_behavior_score(user_id: Optional[int] = None, ip_address: Optional[str] = None) -> int:
    """
    Calculate a behavior score based on recent activity patterns.

    Args:
        user_id: User ID if authenticated
        ip_address: IP address for anonymous users

    Returns:
        Behavior score (0-100, higher = more suspicious)
    """
    if not user_id and not ip_address:
        return 0

    # Look at behavior in the last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    query = db.session.query(
        func.count(UserBehavior.id).label('total_requests'),
        func.sum(UserBehavior.suspicious_score).label('total_suspicious'),
        func.avg(UserBehavior.suspicious_score).label('avg_suspicious'),
        func.count(func.distinct(UserBehavior.endpoint)).label('unique_endpoints'),
        func.count(func.distinct(UserBehavior.method)).label('unique_methods')
    ).filter(UserBehavior.timestamp >= one_hour_ago)

    if user_id:
        query = query.filter(UserBehavior.user_id == user_id)
    elif ip_address:
        query = query.filter(UserBehavior.ip_address == ip_address)

    result = query.first()

    if not result or result.total_requests == 0:
        return 0

    total_requests = result.total_requests or 0
    total_suspicious = result.total_suspicious or 0
    avg_suspicious = result.avg_suspicious or 0
    unique_endpoints = result.unique_endpoints or 0
    unique_methods = result.unique_methods or 0

    score = 0

    # High request volume
    if total_requests > 100:
        score += 30
    elif total_requests > 50:
        score += 15
    elif total_requests > 20:
        score += 5

    # High suspicious score
    if avg_suspicious > 50:
        score += 25
    elif avg_suspicious > 25:
        score += 10

    # Too many unique endpoints (potential scanning)
    if unique_endpoints > 10:
        score += 20
    elif unique_endpoints > 5:
        score += 10

    # Unusual method diversity
    if unique_methods > 4:
        score += 15

    # Check for failed requests pattern
    failed_requests = db.session.query(func.count(UserBehavior.id)).filter(
        UserBehavior.timestamp >= one_hour_ago,
        UserBehavior.status_code >= 400,
        or_(UserBehavior.user_id == user_id, UserBehavior.ip_address == ip_address)
    ).scalar() or 0

    if failed_requests > total_requests * 0.5:  # More than 50% failures
        score += 20

    return min(score, 100)


def get_dynamic_limits(user_id: Optional[int] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
    """
    Get dynamic rate limits based on user behavior.

    Args:
        user_id: User ID if authenticated
        ip_address: IP address for anonymous users

    Returns:
        Dictionary with rate limit configurations
    """
    behavior_score = calculate_behavior_score(user_id, ip_address)

    # Base limits
    limits = {
        'requests_per_minute': 10,
        'requests_per_hour': 100,
        'requests_per_day': 500
    }

    # Adjust limits based on behavior score
    if behavior_score > 75:  # Very suspicious
        limits['requests_per_minute'] = 2
        limits['requests_per_hour'] = 20
        limits['requests_per_day'] = 50
    elif behavior_score > 50:  # Moderately suspicious
        limits['requests_per_minute'] = 5
        limits['requests_per_hour'] = 50
        limits['requests_per_day'] = 200
    elif behavior_score > 25:  # Slightly suspicious
        limits['requests_per_minute'] = 7
        limits['requests_per_hour'] = 75
        limits['requests_per_day'] = 300
    else:  # Normal behavior
        # Check user reputation for bonus limits
        if user_id:
            user = db.session.get(User, user_id)
            if user and user.reputation_points and user.reputation_points > 100:
                limits['requests_per_minute'] = 15
                limits['requests_per_hour'] = 150
                limits['requests_per_day'] = 1000

    return limits


def get_endpoint_specific_limits(endpoint: str) -> Dict[str, Any]:
    """
    Get endpoint-specific rate limits.

    Args:
        endpoint: Flask endpoint name

    Returns:
        Dictionary with endpoint-specific limits
    """
    # Define limits for sensitive endpoints
    endpoint_limits = {
        'main.report_issue': {'requests_per_minute': 5, 'requests_per_hour': 20},
        'main.upvote': {'requests_per_minute': 20, 'requests_per_hour': 100},
        'main.notifications': {'requests_per_minute': 30, 'requests_per_hour': 200},
        'main.reverse_geocode': {'requests_per_minute': 30, 'requests_per_hour': 150},
        'main.check_duplicates': {'requests_per_minute': 10, 'requests_per_hour': 50},
        'main.generate_report': {'requests_per_day': 5},
        'main.login': {'requests_per_minute': 5, 'requests_per_hour': 20},
        'main.register': {'requests_per_hour': 10},
    }

    return endpoint_limits.get(endpoint, {})


def should_track_behavior(endpoint: str, method: str, status_code: int) -> bool:
    """
    Determine if this request should be tracked for behavior analysis.

    Args:
        endpoint: Flask endpoint name
        method: HTTP method
        status_code: Response status code

    Returns:
        True if request should be tracked
    """
    # Don't track static files, health checks, etc.
    if endpoint in ['static', 'main.index'] and method == 'GET' and status_code == 200:
        return False

    # Track all POST/PUT/DELETE requests
    if method in ['POST', 'PUT', 'DELETE']:
        return True

    # Track failed requests
    if status_code >= 400:
        return True

    # Track authentication-related endpoints
    if endpoint in ['main.login', 'main.register', 'main.logout']:
        return True

    return False


def calculate_suspicious_score(endpoint: str, method: str, status_code: int, user_agent: str) -> int:
    """
    Calculate suspicious score for a request.

    Args:
        endpoint: Flask endpoint name
        method: HTTP method
        status_code: Response status code
        user_agent: User agent string

    Returns:
        Suspicious score (0-100)
    """
    score = 0

    # Failed authentication attempts
    if endpoint in ['main.login', 'main.verify_2fa'] and status_code in [401, 403]:
        score += 30

    # Unusual methods
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        score += 20

    # Missing or suspicious user agent
    if not user_agent or len(user_agent) < 10:
        score += 15

    # Known bot patterns in user agent
    suspicious_patterns = ['bot', 'crawler', 'spider', 'scraper']
    if user_agent and any(pattern.lower() in user_agent.lower() for pattern in suspicious_patterns):
        score += 25

    # High-frequency endpoints with failures
    if endpoint in ['main.report_issue', 'main.upvote'] and status_code >= 400:
        score += 10

    return min(score, 100)


def dynamic_limiter(*limits):
    """
    Decorator for dynamic rate limiting based on user behavior.

    Args:
        *limits: Default limits as fallback

    Returns:
        Decorator function
    """
    def decorator(f):
        from flask import current_app, request
        from functools import wraps

        @wraps(f)
        def wrapper(*args, **kwargs):
            limiter = current_app.extensions.get('limiter')
            if not limiter:
                return f(*args, **kwargs)

            # Get dynamic limits based on user behavior
            user_id = None
            ip_address = None

            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                ip_address = get_remote_address()

            dynamic_limits = get_dynamic_limits(user_id, ip_address)
            endpoint_limits = get_endpoint_specific_limits(request.endpoint or '')

            # Combine limits (endpoint-specific take precedence)
            final_limits = {**dynamic_limits, **endpoint_limits}

            # Apply rate limiting
            key_func = user_or_ip_key()

            # Check dynamic limits
            for limit_type, limit_value in final_limits.items():
                if limit_type == 'requests_per_minute':
                    limit_str = f"{limit_value}/minute"
                elif limit_type == 'requests_per_hour':
                    limit_str = f"{limit_value}/hour"
                elif limit_type == 'requests_per_day':
                    limit_str = f"{limit_value}/day"
                else:
                    continue
                try:
                    limiter.check()
                except RateLimitExceeded:
                    raise RateLimitExceeded()

            # Check default limits
            for limit in limits:
                if isinstance(limit, str):
                    try:
                        limiter.check()
                    except RateLimitExceeded:
                        raise RateLimitExceeded()

            return f(*args, **kwargs)

        return wrapper
    return decorator