"""
Defines routes and view functions for the CommunityWatch application.
"""

import os
import json
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, jsonify, \
    send_from_directory, session
from flask_login import current_user, login_user, logout_user, login_required
from flask_wtf.csrf import generate_csrf
from flask_babel import _
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError
from app import db, ai_services, limiter, oauth
from app.cache import cache
from app.rate_limiting import user_or_ip_key, get_dynamic_limits, get_endpoint_specific_limits, dynamic_limiter
from app.schemas import user_registration_schema, issue_report_schema, comment_schema, geofence_schema
from app.forms import RegistrationForm, LoginForm, IssueForm, CommentForm
from app.models import User, Issue, Upvote, Comment, Notification, Badge, UserBadge, Challenge, UserChallenge, Geofence
from app.utils import get_coords_for_location, get_location_for_coords, check_and_award_badges, update_user_challenges, initialize_gamification, get_leaderboard, check_geofence_containment, optimize_route
from app.encryption import encrypt_file, decrypt_file

bp = Blueprint('main', __name__)


@bp.errorhandler(429)
def ratelimit_handler(e):
    """
    Handle 429 Too Many Requests errors from rate limiting.

    Args:
        e: The rate limit error object.

    Returns:
        JSON response with a user-friendly error message.
    """
    current_app.logger.warning(f"Rate limit exceeded: {e.description}")
    return jsonify({'error': 'Too many requests, please try again later'}), 429

# --- MOVED analytics FUNCTION HERE ---
@bp.route('/analytics')
@login_required
def analytics():
    """Render the public community analytics dashboard."""
    # Try to get cached analytics data
    cache_key = 'analytics_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render_template(
            'analytics.html',
            title='Community Analytics',
            **cached_data
        )
    
    status_counts = dict(db.session.query(Issue.status, func.count(Issue.status)).group_by(Issue.status).all())
    top_issues = db.session.scalars(
        select(Issue).where(Issue.status != 'Resolved').options(joinedload(Issue.reporter)).order_by(
            Issue.priority_score.desc(), Issue.upvote_count.desc()).limit(5)
    ).all()
    # Optimize heatmap data query - only select lat/lng for unresolved issues
    heatmap_data = db.session.query(Issue.latitude, Issue.longitude).filter(Issue.status != 'Resolved').all()
    heatmap_data = [[lat, lng] for lat, lng in heatmap_data]
    
    analytics_data = {
        'status_counts': status_counts,
        'top_issues': top_issues,
        'heatmap_data': heatmap_data
    }
    
    # Cache for 1 hour
    cache.set(cache_key, analytics_data, timeout=3600)
    
    return render_template(
        'analytics.html',
        title='Community Analytics',
        **analytics_data
    )

@bp.route('/predictive-analytics')
@login_required
def predictive_analytics():
    """Render predictive analytics dashboard with forecasted hotspots."""
    # Get recent issues for prediction (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_issues = db.session.scalars(
        select(Issue).where(
            Issue.timestamp >= thirty_days_ago
        ).options(joinedload(Issue.reporter)).order_by(Issue.timestamp.desc())
    ).all()

    issues_data = [
        {
            'id': issue.id,
            'lat': issue.latitude,
            'lng': issue.longitude,
            'category': issue.category,
            'timestamp': issue.timestamp.isoformat(),
            'status': issue.status,
            'upvotes': issue.upvote_count or 0
        }
        for issue in recent_issues
    ]

    prediction = ai_services.predict_issue_hotspots(issues_data)

    import json
    hotspots_list = prediction.get('hotspots', [])
    return render_template(
        'predictive_analytics.html',
        title='Predictive Analytics',
        hotspots=hotspots_list,
        hotspots_json=json.dumps(hotspots_list),
        suggestions=prediction.get('suggestions', [])
    )
# --- END MOVED SECTION ---

@bp.route('/')
def index():
    """Render the homepage with an interactive map of issues."""
    issue_form = IssueForm()
    page = request.args.get('page', 1, type=int)
    per_page = 100  # Limit issues shown on map for performance

    # Paginate issues for map display
    issues_query = select(Issue).options(joinedload(Issue.reporter)).order_by(Issue.timestamp.desc())
    issues_paginated = db.paginate(issues_query, page=page, per_page=per_page, error_out=False)

    upvoted_issue_ids = {uv.issue_id for uv in current_user.upvotes.all()} if current_user.is_authenticated else set()

    issues_data = [
        {
            'id': issue.id,
            'lat': issue.latitude,
            'lng': issue.longitude,
            'title': issue.category,
            'upvotes': issue.upvote_count or 0,
            'user_has_voted': issue.id in upvoted_issue_ids,
            'status': issue.status
        }
        for issue in issues_paginated.items
    ]

    return render_template(
        'index.html',
        title='CommunityWatch',
        issue_form=issue_form,
        issues_data=issues_data,
        pagination=issues_paginated
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with form validation."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('main.login'))

        # Check if 2FA is required
        if user.twofa_enabled or (user.is_moderator and user.reputation_points >= 100):
            session['pending_user_id'] = user.id
            return redirect(url_for('main.verify_2fa'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))

    return render_template('login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/login/google')
def login_google():
    """Initiate Google OAuth login."""
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google OAuth is not configured. Please contact the administrator.', 'danger')
        return redirect(url_for('main.login'))
    redirect_uri = url_for('main.authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route('/login/facebook')
def login_facebook():
    """Initiate Facebook OAuth login."""
    redirect_uri = url_for('main.authorize_facebook', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@bp.route('/authorize/google')
def authorize_google():
    """Handle Google OAuth callback."""
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)
    return _oauth_login('google', user_info['sub'], user_info['email'], user_info.get('name'))


@bp.route('/authorize/facebook')
def authorize_facebook():
    """Handle Facebook OAuth callback."""
    token = oauth.facebook.authorize_access_token()
    resp = oauth.facebook.get('me?fields=id,email,name')
    user_info = resp.json()
    return _oauth_login('facebook', user_info['id'], user_info['email'], user_info.get('name'))


def _oauth_login(provider, oauth_id, email, name):
    """Handle OAuth login for both providers."""
    user = db.session.scalar(select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id))
    if not user:
        # Check if email already exists
        existing_user = db.session.scalar(select(User).where(User.email == email))
        if existing_user:
            flash('An account with this email already exists. Please login with password or link your account.', 'warning')
            return redirect(url_for('main.login'))
        # Create new user
        username = name.replace(' ', '_').lower() if name else f"{provider}_{oauth_id}"
        # Ensure unique username
        base_username = username
        counter = 1
        while db.session.scalar(select(User).where(User.username == username)):
            username = f"{base_username}_{counter}"
            counter += 1
        user = User(username=username, email=email, oauth_provider=provider, oauth_id=oauth_id)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')

    # Check if 2FA is required
    if user.twofa_enabled or (user.is_moderator and user.reputation_points >= 100):
        session['pending_user_id'] = user.id
        return redirect(url_for('main.verify_2fa'))

    login_user(user)
    return redirect(url_for('main.index'))


@bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """Setup 2FA for the user."""
    if request.method == 'POST':
        token = request.form.get('token')
        if current_user.verify_twofa(token):
            current_user.twofa_enabled = True
            db.session.commit()
            flash('2FA has been enabled successfully!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid token. Please try again.', 'danger')
    # Generate QR code
    import pyotp
    import qrcode
    import io
    import base64
    if not current_user.twofa_secret:
        current_user.set_twofa_secret()
        db.session.commit()
    totp = pyotp.TOTP(current_user.twofa_secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name='CommunityWatch')
    qr = qrcode.QRCode()
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_code = base64.b64encode(buf.getvalue()).decode('ascii')
    return render_template('setup_2fa.html', qr_code=qr_code, secret=current_user.twofa_secret)


@bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """Verify 2FA token during login."""
    if request.method == 'POST':
        token = request.form.get('token')
        user_id = session.get('pending_user_id')
        if user_id:
            user = db.session.get(User, user_id)
            if user and user.verify_twofa(token):
                login_user(user)
                session.pop('pending_user_id', None)
                return redirect(url_for('main.index'))
            else:
                flash('Invalid 2FA token.', 'danger')
        else:
            flash('Session expired. Please login again.', 'danger')
            return redirect(url_for('main.login'))
    return render_template('verify_2fa.html')


@bp.route('/set_language/<lang>')
def set_language(lang):
    """Set the user's language preference."""
    if lang in current_app.config['LANGUAGES']:
        session['lang'] = lang
        # Force babel to re-evaluate locale on next request by touching session
        session.modified = True
    return redirect(request.referrer or url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration with form validation."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Additional Marshmallow validation
        registration_data = {
            'username': form.username.data,
            'email': form.email.data,
            'password': form.password.data,
            'password2': form.password2.data,
            'data_processing_consent': form.data_processing_consent.data,
            'marketing_consent': form.marketing_consent.data
        }

        try:
            validated_data = user_registration_schema.load(registration_data)
        except ValidationError as err:
            for field, messages in err.messages.items():
                for message in messages:
                    flash(f'{field}: {message}', 'danger')
            return render_template('register.html', title='Register', form=form)

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            data_processing_consent=validated_data['data_processing_consent'],
            marketing_consent=validated_data.get('marketing_consent', False),
            consent_date=datetime.utcnow()
        )
        user.set_password(validated_data['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', title='Register', form=form)


@bp.route('/uploads/<filename>')
def uploaded_file(filename: str):
    """Serve an uploaded file from the upload folder, decrypting if necessary."""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(file_path):
        return "File not found", 404

    # Decrypt the file content
    decrypted_data = decrypt_file(file_path)
    from flask import Response
    # Determine MIME type based on file extension
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'application/octet-stream'

    return Response(decrypted_data, mimetype=mime_type)


@bp.route('/report-issue', methods=['POST'])
@login_required
@dynamic_limiter("10 per minute")
def report_issue():
    """Submit a new issue report with optional photo upload and AI categorization."""
    form = IssueForm()
    if not form.validate_on_submit():
        return jsonify({'success': False, 'errors': form.errors}), 400

    lat = request.form.get('lat', type=float)
    lng = request.form.get('lng', type=float)
    if lat is None or lng is None:
        return jsonify({'success': False, 'error': 'Missing coordinates'}), 400

    # Additional Marshmallow validation
    issue_data = {
        'category': form.category.data or '',
        'description': form.description.data,
        'location_text': form.location_text.data,
        'lat': lat,
        'lng': lng,
        'geojson': form.geojson.data or ''
    }

    try:
        validated_data = issue_report_schema.load(issue_data)
    except ValidationError as err:
        return jsonify({'success': False, 'errors': err.messages}), 400

    filename = None
    image_path = None
    if form.photo.data:
        file_data = form.photo.data
        # Validate file size (5MB limit)
        max_file_size = 5 * 1024 * 1024  # 5MB
        if len(file_data.read()) > max_file_size:
            return jsonify({'success': False, 'error': 'File size exceeds 5MB limit'}), 400
        file_data.seek(0)  # Reset file pointer after reading
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file_data.filename and file_data.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed types: png, jpg, jpeg, gif'}), 400
        
        filename = secure_filename(file_data.filename)
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file_data.save(image_path)
        # Encrypt the image file
        encrypt_file(image_path)

    # Automated moderation
    moderation_result = ai_services.moderate_content(form.description.data, image_path)
    if not moderation_result.get('is_appropriate', True):
        return jsonify({'success': False, 'error': f'Content flagged as inappropriate: {moderation_result.get("reason", "Unknown reason")}'}), 400

    # Smart categorization using AI
    category = form.category.data if form.category.data else None
    if not category:
        category = ai_services.categorize_issue(form.description.data, image_path)
    else:
        # If user selected a category, validate it
        if category not in Issue.VALID_CATEGORIES:
            category = 'Other'

    issue = Issue(
        category=category,
        description=form.description.data,
        latitude=lat,
        longitude=lng,
        reporter=current_user,
        location_text=form.location_text.data,
        image_filename=filename,
        geojson=json.loads(form.geojson.data) if form.geojson.data else None
    )
    issue.reporter.reputation_points = (issue.reporter.reputation_points or 0) + 5
    # Generate embedding for search
    issue.generate_and_set_embedding()
    db.session.add(issue)
    db.session.commit()

    # Check for geofence notifications
    geofences = Geofence.query.filter_by(notify_on_issue=True).all()
    for geofence in geofences:
        if check_geofence_containment(issue.latitude, issue.longitude, geofence.geometry):
            geofence.user.add_notification(
                'geofence_issue',
                {
                    'issue_id': issue.id,
                    'issue_category': issue.category,
                    'geofence_name': geofence.name,
                    'lat': issue.latitude,
                    'lng': issue.longitude
                }
            )

    # Check for badges and challenges
    check_and_award_badges(issue.reporter)
    update_user_challenges(issue.reporter)

    # Invalidate analytics cache when a new issue is reported
    cache.delete('analytics_data')

    return jsonify({
        'success': True,
        'issue': {
            'id': issue.id,
            'title': issue.category,
            'lat': issue.latitude,
            'lng': issue.longitude
        }
    })


@bp.route('/upvote/<int:issue_id>', methods=['POST'])
@login_required
@dynamic_limiter("20 per minute")
def upvote(issue_id: int):
    """Toggle upvote for an issue and update reputation points."""
    issue = db.session.get(Issue, issue_id)
    if not issue:
        return jsonify({'success': False, 'error': 'Issue not found'}), 404

    # Check upvote cooldown (5 seconds between upvotes)
    from datetime import timedelta
    if current_user.last_upvote_time and datetime.utcnow() - current_user.last_upvote_time < timedelta(seconds=5):
        return jsonify({'success': False, 'error': 'Please wait before upvoting again'}), 429

    issue.upvote_count = issue.upvote_count or 0
    issue.reporter.reputation_points = issue.reporter.reputation_points or 0

    existing_upvote = current_user.upvotes.filter_by(issue_id=issue_id).first()
    if existing_upvote:
        db.session.delete(existing_upvote)
        issue.upvote_count -= 1
        issue.reporter.reputation_points -= 2
        voted = False
    else:
        new_upvote = Upvote(voter=current_user, issue_id=issue_id)
        db.session.add(new_upvote)
        issue.upvote_count += 1
        issue.reporter.reputation_points += 2
        voted = True

    current_user.last_upvote_time = datetime.utcnow()
    db.session.commit()

    # Check for badges and challenges
    check_and_award_badges(issue.reporter)
    update_user_challenges(issue.reporter)

    # Note: Not invalidating analytics cache on upvotes to improve cache effectiveness
    # Analytics include top issues which are affected by upvotes, but cache staleness is acceptable

    return jsonify({'success': True, 'upvote_count': issue.upvote_count, 'voted': voted})


@bp.route('/issue/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def view_issue(issue_id: int):
    """Display an issue and handle comment submission."""
    issue = db.session.get(Issue, issue_id, options=[
        joinedload(Issue.comments).joinedload(Comment.author),
        joinedload(Issue.reporter)
    ])
    if not issue:
        flash('Issue not found.', 'danger')
        return redirect(url_for('main.index'))

    form = CommentForm()
    if form.validate_on_submit():
        # Additional Marshmallow validation
        comment_data = {'body': form.body.data}
        try:
            validated_data = comment_schema.load(comment_data)
        except ValidationError as err:
            flash('Comment validation failed.', 'danger')
            return render_template('view_issue.html', title=issue.category, issue=issue, form=form, comments=comments)

        comment = Comment(
            body=validated_data['body'],
            issue=issue,
            author=current_user
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.', 'success')
        return redirect(url_for('main.view_issue', issue_id=issue.id))

    comments = sorted(issue.comments, key=lambda c: c.timestamp)
    return render_template('view_issue.html', title=issue.category, issue=issue, form=form, comments=comments)


@bp.route('/issue/<int:issue_id>/update_status', methods=['POST'])
@login_required
def update_status(issue_id: int):
    """Update issue status and notify relevant users (moderator only)."""
    if not current_user.is_moderator:
        flash('Permission denied.', 'danger')
        return redirect(url_for('main.index'))

    issue = db.session.get(Issue, issue_id, options=[joinedload(Issue.reporter)])
    if not issue:
        flash('Issue not found.', 'danger')
        return redirect(url_for('main.view_issue', issue_id=issue_id))

    new_status = request.form.get('status')
    valid_statuses = {'Reported', 'In Progress', 'Resolved'}
    if new_status not in valid_statuses:
        flash('Invalid status.', 'danger')
        return redirect(url_for('main.view_issue', issue_id=issue_id))

    old_status = issue.status
    issue.status = new_status
    if new_status == 'Resolved':
        issue.resolved_at = datetime.utcnow()
        issue.reporter.reputation_points = (issue.reporter.reputation_points or 0) + 20

    # Log the status change
    current_app.logger.info(f"Moderator {current_user.username} changed issue {issue.id} status from '{old_status}' to '{new_status}'")

    recipients = {issue.reporter}
    upvoters = db.session.scalars(
        select(User).join(Upvote).where(Upvote.issue_id == issue.id).options(joinedload(User.upvotes))
    ).all()
    recipients.update(upvoters)

    for user in recipients:
        user.add_notification(
            'status_update',
            {'issue_id': issue.id, 'issue_category': issue.category, 'status': new_status}
        )

    db.session.commit()

    # Check for badges and challenges
    check_and_award_badges(issue.reporter)
    update_user_challenges(issue.reporter)

    # Invalidate analytics cache when status changes
    cache.delete('analytics_data')

    return redirect(url_for('main.view_issue', issue_id=issue_id))


@bp.route('/search')
def search():
    """Handle geo-semantic search for issues."""
    query = request.args.get('q', '', type=str).strip()
    location_query = request.args.get('loc', '', type=str).strip()

    if not query and not location_query:
        return redirect(url_for('main.index'))

    base_query = select(Issue).options(joinedload(Issue.reporter))
    if location_query:
        coords = get_coords_for_location(location_query)
        if coords:
            lat, lng = coords
            radius = 0.05
            base_query = base_query.where(
                Issue.latitude.between(lat - radius, lat + radius),
                Issue.longitude.between(lng - radius, lng + radius)
            )
        else:
            flash(f"Could not find location: {location_query}", 'warning')
            return render_template('search_results.html', title='Search Results', results=[], query=query,
                                   location=location_query)

    issues = db.session.scalars(base_query.order_by(Issue.timestamp.desc())).all()
    if query and issues:
        query_embedding = ai_services.generate_embedding(query, task_type='RETRIEVAL_QUERY')
        if query_embedding:
            query_vector = np.array(query_embedding)

            def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
                """Calculate cosine similarity between two vectors."""
                return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

            similarities = {
                issue.id: cosine_similarity(query_vector, np.array(issue.embedding))
                for issue in issues if issue.embedding
            }

            threshold = 0.6
            relevant_ids = {sid: score for sid, score in similarities.items() if score > threshold}
            sorted_ids = sorted(relevant_ids, key=relevant_ids.get, reverse=True)
            issue_map = {issue.id: issue for issue in issues}
            issues = [issue_map[sid] for sid in sorted_ids if sid in issue_map]
        else:
            issues = []

    return render_template('search_results.html', title='Search Results', results=issues, query=query,
                           location=location_query)


@bp.route('/notification-history')
@login_required
def notification_history():
    """Render the user's notification history with pagination."""
    page = request.args.get('page', 1, type=int)
    notifications = current_user.notifications.order_by(Notification.timestamp.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template('notification_history.html', title='Notification History', notifications=notifications)


@bp.route('/notifications')
@login_required
@dynamic_limiter("30 per minute")
def notifications():
    """Fetch user notifications since a given timestamp."""
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(Notification.timestamp > since).order_by(
        Notification.timestamp.asc()).all()

    return jsonify([
        {
            'name': n.name,
            'data': n.get_data(),
            'timestamp': n.timestamp
        }
        for n in notifications
    ])


@bp.route('/user/<username>')
@login_required
def user_profile(username: str):
    """Display a user's profile and their reported issues."""
    user = db.session.scalar(
        select(User).where(User.username == username).options(joinedload(User.issues))
    )
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.index'))

    issues = sorted(user.issues, key=lambda i: i.timestamp, reverse=True)  # Sort issues in Python
    user_badges = [ub.badge for ub in user.badges]
    return render_template('user_profile.html', title=f"{user.username}'s Profile", user=user, issues=issues, user_badges=user_badges)


@bp.route('/reverse-geocode', methods=['POST'])
@login_required
@dynamic_limiter("30 per minute")
def reverse_geocode():
    """Get an address from coordinates via reverse geocoding."""
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        data = {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat is None or lng is None:
        return jsonify({'error': 'Missing coordinates'}), 400

    try:
        lat_f, lng_f = float(lat), float(lng)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    address = get_location_for_coords(lat_f, lng_f)
    return jsonify({'address': address or 'Unknown address'})


@bp.route('/check-duplicates', methods=['POST'])
@login_required
@limiter.limit("10 per minute", key_func=user_or_ip_key)
def check_duplicates():
    """Check if a new issue is a duplicate of nearby issues."""
    data = request.get_json() or {}
    try:
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinates'}), 400

    description = data.get('description', '')
    radius = current_app.config['DUPLICATE_DETECTION_RADIUS']
    nearby_issues = db.session.scalars(
        select(Issue).where(
            Issue.latitude.between(lat - radius, lat + radius),
            Issue.longitude.between(lng - radius, lng + radius)
        ).options(joinedload(Issue.reporter))
    ).all()

    if not nearby_issues:
        return jsonify({'is_duplicate': False})

    existing_issues_data = [
        {'id': issue.id, 'title': issue.category, 'description': issue.description}
        for issue in nearby_issues
    ]
    result = ai_services.find_duplicate_issue(description, existing_issues_data)

    if result.get('is_duplicate'):
        duplicate_issue = db.session.get(Issue, result.get('duplicate_id'), options=[joinedload(Issue.reporter)])
        if duplicate_issue:
            result['duplicate_title'] = duplicate_issue.category

    return jsonify(result)


@bp.route('/generate-report', methods=['POST'])
@limiter.limit("5 per day", key_func=user_or_ip_key)
def generate_report():
    """Generate a weekly AI summary report of recent issues."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    recent_issues = db.session.scalars(
        select(Issue).where(Issue.timestamp.between(start_date, end_date)).options(joinedload(Issue.reporter)).order_by(Issue.timestamp.desc())
    ).all()

    if not recent_issues:
        return jsonify({'report': 'No new issues reported in the last 7 days'})

    issues_by_cat = {}
    for issue in recent_issues:
        issues_by_cat[issue.category] = issues_by_cat.get(issue.category, 0) + 1

    top_issue = max(recent_issues, key=lambda issue: issue.upvote_count or 0)
    date_format = '%B %d, %Y'
    data_summary = (
        f"Date Range: {start_date.strftime(date_format)} to {end_date.strftime(date_format)}\n"
        f"- Total new issues: {len(recent_issues)}\n"
        f"- Breakdown by category: {issues_by_cat}\n"
        f"- Most upvoted new issue: '{top_issue.category}' with {top_issue.upvote_count or 0} upvotes"
    )

    report = ai_services.generate_weekly_report(data_summary)
    return jsonify({'report': report})


@bp.route('/leaderboard')
@login_required
def leaderboard():
    """Display the reputation leaderboard."""
    leaderboard_data = get_leaderboard()
    return render_template('leaderboard.html', title='Leaderboard', leaderboard=leaderboard_data)


@bp.route('/badges')
@login_required
def badges():
    """Display all available badges."""
    all_badges = Badge.query.all()
    user_badges = {ub.badge_id for ub in current_user.badges}
    return render_template('badges.html', title='Badges', badges=all_badges, user_badges=user_badges)


@bp.route('/challenges')
@login_required
def challenges():
    """Display user's challenges."""
    user_challenges = UserChallenge.query.filter_by(user_id=current_user.id).join(Challenge).all()
    return render_template('challenges.html', title='Challenges', challenges=user_challenges)


@bp.route('/geofences', methods=['GET', 'POST'])
@login_required
def manage_geofences():
    """Manage user's geofences."""
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name')
        geometry = data.get('geometry')

        if not name or not geometry:
            return jsonify({'success': False, 'error': 'Name and geometry required'}), 400

        # Additional Marshmallow validation
        geofence_data = {
            'name': name,
            'geometry': geometry,
            'notify_on_issue': data.get('notify_on_issue', True)
        }

        try:
            validated_data = geofence_schema.load(geofence_data)
        except ValidationError as err:
            return jsonify({'success': False, 'errors': err.messages}), 400

        geofence = Geofence(
            user=current_user,
            name=validated_data['name'],
            geometry=validated_data['geometry'],
            notify_on_issue=validated_data.get('notify_on_issue', True)
        )
        db.session.add(geofence)
        db.session.commit()

        return jsonify({'success': True, 'geofence_id': geofence.id})

    geofences = Geofence.query.filter_by(user_id=current_user.id).all()
    return render_template('geofences.html', title='My Geofences', geofences=geofences)


@bp.route('/geofence/<int:geofence_id>', methods=['DELETE'])
@login_required
def delete_geofence(geofence_id: int):
    """Delete a geofence."""
    geofence = Geofence.query.filter_by(id=geofence_id, user_id=current_user.id).first()
    if not geofence:
        return jsonify({'success': False, 'error': 'Geofence not found'}), 404

    db.session.delete(geofence)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/optimize-route', methods=['POST'])
@login_required
def optimize_route_endpoint():
    """Optimize route for nearby unresolved issues (moderators only)."""
    if not current_user.is_moderator:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403

    data = request.get_json() or {}
    center_lat = data.get('lat')
    center_lng = data.get('lng')
    radius_km = data.get('radius', 5.0)  # Default 5km radius

    if center_lat is None or center_lng is None:
        return jsonify({'success': False, 'error': 'Center coordinates required'}), 400

    # Find nearby unresolved issues
    from sqlalchemy import func
    nearby_issues = db.session.scalars(
        select(Issue).where(
            Issue.status != 'Resolved',
            func.acos(
                func.sin(func.radians(center_lat)) * func.sin(func.radians(Issue.latitude)) +
                func.cos(func.radians(center_lat)) * func.cos(func.radians(Issue.latitude)) *
                func.cos(func.radians(Issue.longitude) - func.radians(center_lng))
            ) * 6371 <= radius_km  # 6371 is Earth's radius in km
        ).options(joinedload(Issue.reporter))
    ).all()

    if not nearby_issues:
        return jsonify({'success': False, 'error': 'No nearby issues found'})

    # Optimize route
    optimized_issues = optimize_route(list(nearby_issues), center_lat, center_lng)

    route_data = [
        {
            'id': issue.id,
            'category': issue.category,
            'description': issue.description[:100] + '...' if len(issue.description) > 100 else issue.description,
            'lat': issue.latitude,
            'lng': issue.longitude,
            'status': issue.status,
            'upvotes': issue.upvote_count or 0
        }
        for issue in optimized_issues
    ]

    return jsonify({'success': True, 'route': route_data})


@bp.route('/export-data', methods=['GET'])
@login_required
def export_data():
    """Export user's personal data as JSON."""
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'reputation_points': current_user.reputation_points,
        'role': current_user.role,
        'twofa_enabled': current_user.twofa_enabled,
        'data_processing_consent': current_user.data_processing_consent,
        'marketing_consent': current_user.marketing_consent,
        'consent_date': current_user.consent_date.isoformat() if current_user.consent_date else None,
        'registration_date': current_user.id,  # Assuming id relates to registration order
        'issues': [
            {
                'id': issue.id,
                'category': issue.category,
                'description': issue.description,
                'latitude': issue.latitude,
                'longitude': issue.longitude,
                'location_text': issue.location_text,
                'timestamp': issue.timestamp.isoformat(),
                'status': issue.status,
                'upvote_count': issue.upvote_count
            }
            for issue in current_user.issues
        ],
        'comments': [
            {
                'id': comment.id,
                'body': comment.body,
                'timestamp': comment.timestamp,
                'issue_id': comment.issue_id
            }
            for comment in db.session.scalars(select(Comment).where(Comment.author_id == current_user.id))
        ],
        'upvotes': [
            {
                'issue_id': upvote.issue_id,
                'timestamp': upvote.id  # Assuming id is timestamp-related
            }
            for upvote in current_user.upvotes
        ],
        'notifications': [
            {
                'name': n.name,
                'data': n.get_data(),
                'timestamp': n.timestamp
            }
            for n in current_user.notifications
        ],
        'badges': [
            {
                'name': ub.badge.name,
                'description': ub.badge.description,
                'awarded_at': ub.awarded_at.isoformat()
            }
            for ub in current_user.badges
        ],
        'geofences': [
            {
                'name': gf.name,
                'geometry': gf.geometry,
                'notify_on_issue': gf.notify_on_issue
            }
            for gf in current_user.geofences
        ]
    }

    from flask import Response
    import json
    response = Response(
        json.dumps(user_data, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=user_data.json'}
    )
    return response


@bp.route('/get-csrf-token', methods=['GET'])
@login_required
def get_csrf_token():
    """Provide a CSRF token for AJAX requests."""
    token = generate_csrf()
    return jsonify({'csrf_token': token})


@bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user's account and all associated data."""
    # Delete associated data
    # Issues and comments/upvotes will be cascade deleted due to relationships

    # Delete notifications
    Notification.query.filter_by(user_id=current_user.id).delete()

    # Delete user badges
    UserBadge.query.filter_by(user_id=current_user.id).delete()

    # Delete user challenges
    UserChallenge.query.filter_by(user_id=current_user.id).delete()

    # Delete geofences
    Geofence.query.filter_by(user_id=current_user.id).delete()

    # Delete user
    db.session.delete(current_user)
    db.session.commit()

    logout_user()
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('main.index'))

