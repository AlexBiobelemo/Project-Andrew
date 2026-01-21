"""
Utility functions for geocoding, reverse geocoding, and location density in the CommunityWatch application.
"""

from typing import Tuple, Optional, List
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from flask import current_app
from app import db
from app.models import Issue, User, Badge, UserBadge, Challenge, UserChallenge, Geofence
from sqlalchemy import func
from shapely.geometry import Point, Polygon
from shapely import wkb
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def get_coords_for_location(location_name: str) -> Optional[Tuple[float, float]]:
    """
    Convert a location name to latitude and longitude coordinates.

    Args:
        location_name: The name or address of the location to geocode.

    Returns:
        A tuple of (latitude, longitude) if successful, None otherwise.
    """
    try:
        geolocator = Nominatim(user_agent="community_watch_app")
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        current_app.logger.warning(f"Geocoding failed for location: {location_name}")
        return None
    except Exception as e:
        current_app.logger.error(f"Geocoding error for {location_name}: {str(e)}")
        return None

def get_location_for_coords(lat: float, lng: float) -> str:
    """
    Convert coordinates to a human-readable address.

    Args:
        lat: Latitude of the location.
        lng: Longitude of the location.

    Returns:
        A string containing the address or an error message if the lookup fails.
    """
    try:
        geolocator = Nominatim(user_agent="community_watch_app")
        location = geolocator.reverse((lat, lng), exactly_one=True)
        if location:
            return location.address
        current_app.logger.warning(f"Reverse geocoding failed for coordinates: ({lat}, {lng})")
        return "Unknown location"
    except Exception as e:
        current_app.logger.error(f"Reverse geocoding error for ({lat}, {lng}): {str(e)}")
        return "Could not determine address"

def calculate_location_density(lat: float, lng: float, radius_km: float = 1.0) -> int:
    """
    Calculate the number of issues within a given radius of a location.

    Args:
        lat: Latitude of the center point.
        lng: Longitude of the center point.
        radius_km: Radius in kilometers (default 1 km).

    Returns:
        Number of issues within the radius.
    """
    # Get all issues
    issues = Issue.query.all()
    count = 0
    for issue in issues:
        distance = geodesic((lat, lng), (issue.latitude, issue.longitude)).km
        if distance <= radius_km:
            count += 1
    return count


def initialize_gamification():
    """Initialize default badges and challenges if they don't exist."""
    # Check if tables exist (to avoid errors during db init)
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    if not inspector.has_table('badge'):
        return

    # Badges
    badges_data = [
        {"name": "First Reporter", "description": "Reported your first issue", "criteria": "issues_count >= 1"},
        {"name": "Active Reporter", "description": "Reported 10 issues", "criteria": "issues_count >= 10"},
        {"name": "Community Hero", "description": "Reported 50 issues", "criteria": "issues_count >= 50"},
        {"name": "Upvote Collector", "description": "Received 50 upvotes on your issues", "criteria": "total_upvotes >= 50"},
        {"name": "Resolution Master", "description": "Had 10 issues resolved", "criteria": "resolved_issues >= 10"},
    ]
    for badge_data in badges_data:
        if not Badge.query.filter_by(name=badge_data["name"]).first():
            badge = Badge(**badge_data)
            db.session.add(badge)

    # Challenges
    challenges_data = [
        {"name": "Report 5 Issues", "description": "Report 5 issues to get started", "criteria": "issues_count >= 5", "reward_points": 10},
        {"name": "Get 20 Upvotes", "description": "Receive 20 upvotes on your issues", "criteria": "total_upvotes >= 20", "reward_points": 15},
        {"name": "Resolve Issues", "description": "Have 5 of your issues resolved", "criteria": "resolved_issues >= 5", "reward_points": 20},
    ]
    for challenge_data in challenges_data:
        if not Challenge.query.filter_by(name=challenge_data["name"]).first():
            challenge = Challenge(**challenge_data)
            db.session.add(challenge)

    db.session.commit()


def check_and_award_badges(user: User):
    """Check if user qualifies for any badges and award them."""
    # Calculate user stats
    issues_count = len(user.issues)
    total_upvotes = sum(issue.upvote_count for issue in user.issues)
    resolved_issues = sum(1 for issue in user.issues if issue.status == 'Resolved')

    badges = Badge.query.all()
    for badge in badges:
        # Check if already has the badge
        if UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
            continue

        # Evaluate criteria (simple eval for now, in production use safer method)
        criteria = badge.criteria.replace('issues_count', str(issues_count)).replace('total_upvotes', str(total_upvotes)).replace('resolved_issues', str(resolved_issues))
        if eval(criteria):
            user_badge = UserBadge(user=user, badge=badge)
            db.session.add(user_badge)
            # Optionally add notification
            user.add_notification('badge_awarded', {'badge_name': badge.name, 'badge_description': badge.description})


def update_user_challenges(user: User):
    """Update progress on user's challenges."""
    # Calculate user stats
    issues_count = len(user.issues)
    total_upvotes = sum(issue.upvote_count for issue in user.issues)
    resolved_issues = sum(1 for issue in user.issues if issue.status == 'Resolved')

    challenges = Challenge.query.filter_by(active=True).all()
    for challenge in challenges:
        user_challenge = UserChallenge.query.filter_by(user_id=user.id, challenge_id=challenge.id).first()
        if not user_challenge:
            user_challenge = UserChallenge(user=user, challenge=challenge)
            db.session.add(user_challenge)

        if user_challenge.completed_at:
            continue

        # Update progress (for simplicity, set progress to the value)
        if 'issues_count' in challenge.criteria:
            user_challenge.progress = issues_count
        elif 'total_upvotes' in challenge.criteria:
            user_challenge.progress = total_upvotes
        elif 'resolved_issues' in challenge.criteria:
            user_challenge.progress = resolved_issues

        # Check if completed
        criteria = challenge.criteria.replace('issues_count', str(issues_count)).replace('total_upvotes', str(total_upvotes)).replace('resolved_issues', str(resolved_issues))
        if eval(criteria) and not user_challenge.completed_at:
            user_challenge.completed_at = db.func.now()
            user.reputation_points = (user.reputation_points or 0) + challenge.reward_points
            user.add_notification('challenge_completed', {'challenge_name': challenge.name, 'reward_points': challenge.reward_points})

    db.session.commit()


def get_leaderboard(limit: int = 10) -> list:
    """Get the top users by reputation points."""
    users = User.query.order_by(User.reputation_points.desc()).limit(limit).all()
    leaderboard = []
    for i, user in enumerate(users, 1):
        leaderboard.append({
            'rank': i,
            'username': user.username,
            'reputation_points': user.reputation_points or 0,
            'issues_count': len(user.issues)
        })
    return leaderboard


def check_geofence_containment(lat: float, lng: float, geofence_geometry: dict) -> bool:
    """
    Check if a point is within a geofence polygon.

    Args:
        lat: Latitude of the point.
        lng: Longitude of the point.
        geofence_geometry: GeoJSON geometry dict.

    Returns:
        True if point is within the geofence, False otherwise.
    """
    try:
        point = Point(lng, lat)  # Note: shapely uses (x, y) which is (lng, lat)
        if geofence_geometry['type'] == 'Polygon':
            coords = geofence_geometry['coordinates'][0]  # Outer ring
            polygon = Polygon(coords)
            return polygon.contains(point)
        return False
    except Exception as e:
        current_app.logger.error(f"Error checking geofence containment: {str(e)}")
        return False


def optimize_route(issues: List[Issue], start_lat: float = None, start_lng: float = None) -> List[Issue]:
    """
    Optimize the route to visit multiple issues using TSP.

    Args:
        issues: List of Issue objects to visit.
        start_lat: Starting latitude (optional).
        start_lng: Starting longitude (optional).

    Returns:
        Optimized list of issues in visit order.
    """
    if len(issues) <= 1:
        return issues

    # Extract coordinates
    coords = [(issue.latitude, issue.longitude) for issue in issues]
    if start_lat is not None and start_lng is not None:
        coords.insert(0, (start_lat, start_lng))
        issues.insert(0, None)  # Placeholder for start point

    n = len(coords)

    # Create distance matrix
    distance_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                distance_matrix[i][j] = geodesic(coords[i], coords[j]).meters

    # Create routing model
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        index = routing.Start(0)
        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index > 0 or start_lat is None:  # Skip start point if it was added
                route.append(issues[node_index])
            index = solution.Value(routing.NextVar(index))
        return [issue for issue in route if issue is not None]
    else:
        # Return original order if optimization fails
        return [issue for issue in issues if issue is not None]