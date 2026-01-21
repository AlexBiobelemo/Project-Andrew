"""
Database models for the CommunityWatch application.
"""

from typing import Dict, Any
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON
from app import db
from app.encryption import encrypt_data, decrypt_data

class User(UserMixin, db.Model):
    """
    User model for authentication and issue reporting.

    Attributes:
        id: Unique identifier for the user.
        username: Unique username for the user.
        email: Unique email address for the user.
        password_hash: Hashed password for authentication (nullable for OAuth users).
        reputation_points: User's reputation score based on contributions.
        role: User's role for RBAC (user, moderator, admin).
        oauth_provider: OAuth provider (google, facebook, or None).
        oauth_id: OAuth provider's user ID.
        twofa_secret: Secret for TOTP 2FA.
        twofa_enabled: Whether 2FA is enabled.
        issues: Issues reported by the user.
        upvotes: Upvotes cast by the user.
        notifications: Notifications received by the user.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    _encrypted_email = db.Column(db.String(256), index=True, unique=True, nullable=False)  # Encrypted email
    password_hash = db.Column(db.String(256), nullable=True)
    reputation_points = db.Column(db.Integer, index=True, default=0)
    role = db.Column(db.String(20), index=True, default='user', nullable=False)
    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(100), nullable=True)
    _encrypted_twofa_secret = db.Column(db.String(256), nullable=True)  # Encrypted 2FA secret
    twofa_enabled = db.Column(db.Boolean, default=False)
    data_processing_consent = db.Column(db.Boolean, default=False)
    marketing_consent = db.Column(db.Boolean, default=False)
    consent_date = db.Column(db.DateTime, nullable=True)
    last_upvote_time = db.Column(db.DateTime, nullable=True)
    issues = db.relationship('Issue', back_populates='reporter', cascade='all, delete-orphan')  # Removed lazy='dynamic'
    upvotes = db.relationship('Upvote', back_populates='voter', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def email(self):
        """Get decrypted email."""
        return decrypt_data(self._encrypted_email) if self._encrypted_email else None

    @email.setter
    def email(self, value):
        """Set encrypted email."""
        self._encrypted_email = encrypt_data(value) if value else None

    @property
    def twofa_secret(self):
        """Get decrypted 2FA secret."""
        return decrypt_data(self._encrypted_twofa_secret) if self._encrypted_twofa_secret else None

    @twofa_secret.setter
    def twofa_secret(self, value):
        """Set encrypted 2FA secret."""
        self._encrypted_twofa_secret = encrypt_data(value) if value else None

    def set_password(self, password: str) -> None:
        """Set the user's password by hashing it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the provided password against the stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_moderator(self) -> bool:
        """Check if user has moderator or admin role."""
        return self.role in ['moderator', 'admin']

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    def set_twofa_secret(self) -> str:
        """Generate and set a new TOTP secret."""
        import pyotp
        self.twofa_secret = pyotp.random_base32()
        return self.twofa_secret

    def verify_twofa(self, token: str) -> bool:
        """Verify a TOTP token."""
        if not self.twofa_secret:
            return False
        import pyotp
        totp = pyotp.TOTP(self.twofa_secret)
        return totp.verify(token)

    def add_notification(self, name: str, data: Dict[str, Any]) -> None:
        """
        Add a notification for the user.

        Args:
            name: The name/type of the notification.
            data: The notification data as a dictionary.
        """
        notification = Notification(name=name, data=data, user=self)
        db.session.add(notification)

    def get_notifications_since(self, since: float) -> list:
        """
        Retrieve notifications since a given timestamp.

        Args:
            since: Unix timestamp to filter notifications.

        Returns:
            List of notifications newer than the given timestamp.
        """
        return self.notifications.filter(Notification.timestamp > since).order_by(Notification.timestamp.asc()).all()

class Issue(db.Model):
    """
    Issue model for community-reported issues.

    Attributes:
        id: Unique identifier for the issue.
        category: Type of issue (e.g., Pothole, Graffiti).
        description: Detailed description of the issue.
        latitude: Latitude coordinate of the issue location.
        longitude: Longitude coordinate of the issue location.
        location_text: Optional human-readable location description.
        image_filename: Filename of the uploaded image (if any).
        timestamp: When the issue was reported.
        status: Current status of the issue (Reported, In Progress, Resolved).
        upvote_count: Number of upvotes received.
        embedding: AI-generated embedding for semantic search.
        geojson: Optional GeoJSON data for the issue location.
        reporter_id: Foreign key to the reporting user.
        reporter: The user who reported the issue.
        comments: Comments associated with the issue.
        upvotes: Upvotes associated with the issue.
    """
    __tablename__ = 'issue'

    VALID_CATEGORIES = [
        'Blocked Drainage', 'Broken Park Bench', 'Broken Streetlight',
        'Broken Traffic Light', 'Damaged Public Property', 'Faded Road Markings',
        'Fallen Tree', 'Flooding', 'Graffiti', 'Leaking Pipe',
        'Overgrown Vegetation', 'Pothole', 'Power Line Down',
        'Stray Animal Concern', 'Waste Dumping', 'Other'
    ]

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), index=True, nullable=False)
    _encrypted_description = db.Column(db.Text, nullable=False)  # Encrypted description
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    _encrypted_location_text = db.Column(db.String(256))  # Encrypted location text
    image_filename = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(64), index=True, default='Reported', nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    upvote_count = db.Column(db.Integer, index=True, default=0)
    priority_score = db.Column(db.Float, index=True, default=0.0)
    embedding = db.Column(db.PickleType)
    geojson = db.Column(JSON)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    reporter = db.relationship('User', back_populates='issues')
    comments = db.relationship('Comment', back_populates='issue', cascade='all, delete-orphan')
    upvotes = db.relationship('Upvote', back_populates='issue', cascade='all, delete-orphan')

    @property
    def description(self):
        """Get decrypted description."""
        return decrypt_data(self._encrypted_description) if self._encrypted_description else None

    @description.setter
    def description(self, value):
        """Set encrypted description."""
        self._encrypted_description = encrypt_data(value) if value else None

    @property
    def location_text(self):
        """Get decrypted location text."""
        return decrypt_data(self._encrypted_location_text) if self._encrypted_location_text else None

    @location_text.setter
    def location_text(self, value):
        """Set encrypted location text."""
        self._encrypted_location_text = encrypt_data(value) if value else None

    def generate_and_set_embedding(self) -> None:
        """
        Generate and set an AI embedding for the issue description.
        """
        from app.ai_services import generate_embedding
        text = f"{self.category}: {self.description}"
        self.embedding = generate_embedding(text, task_type='RETRIEVAL_DOCUMENT')

class Comment(db.Model):
    """
    Comment model for user comments on issues.

    Attributes:
        id: Unique identifier for the comment.
        body: The comment text.
        timestamp: When the comment was posted.
        issue_id: Foreign key to the associated issue.
        author_id: Foreign key to the commenting user.
        issue: The associated issue.
        author: The user who posted the comment.
    """
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    _encrypted_body = db.Column(db.Text, nullable=False)  # Encrypted body
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), index=True, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    issue = db.relationship('Issue', back_populates='comments')
    author = db.relationship('User')

    @property
    def body(self):
        """Get decrypted body."""
        return decrypt_data(self._encrypted_body) if self._encrypted_body else None

    @body.setter
    def body(self, value):
        """Set encrypted body."""
        self._encrypted_body = encrypt_data(value) if value else None

class Upvote(db.Model):
    """
    Upvote model for user upvotes on issues.

    Attributes:
        id: Unique identifier for the upvote.
        voter_id: Foreign key to the user who upvoted.
        issue_id: Foreign key to the upvoted issue.
        voter: The user who upvoted.
        issue: The associated issue.
    """
    __tablename__ = 'upvote'

    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey('issue.id'), index=True, nullable=False)
    voter = db.relationship('User', back_populates='upvotes')
    issue = db.relationship('Issue', back_populates='upvotes')

class Notification(db.Model):
    """
    Notification model for user notifications.

    Attributes:
        id: Unique identifier for the notification.
        name: The type/name of the notification.
        data: JSON data associated with the notification.
        timestamp: When the notification was created.
        user_id: Foreign key to the user receiving the notification.
        user: The associated user.
    """
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    data = db.Column(JSON, nullable=False)
    timestamp = db.Column(db.Float, index=True, default=lambda: datetime.utcnow().timestamp(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True, nullable=False)
    user = db.relationship('User', back_populates='notifications')

    def get_data(self) -> Dict[str, Any]:
        """Return the notification data as a dictionary."""
        return self.data or {}


class Badge(db.Model):
    """
    Badge model for gamification achievements.

    Attributes:
        id: Unique identifier for the badge.
        name: Name of the badge.
        description: Description of the badge.
        icon: Filename of the badge icon.
        criteria: Criteria for earning the badge.
    """
    __tablename__ = 'badge'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(64))
    criteria = db.Column(db.Text, nullable=False)


class UserBadge(db.Model):
    """
    UserBadge model for associating users with earned badges.

    Attributes:
        id: Unique identifier.
        user_id: Foreign key to the user.
        badge_id: Foreign key to the badge.
        awarded_at: When the badge was awarded.
        user: The associated user.
        badge: The associated badge.
    """
    __tablename__ = 'user_badge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref='badges')
    badge = db.relationship('Badge', backref='users')


class Challenge(db.Model):
    """
    Challenge model for gamification tasks.

    Attributes:
        id: Unique identifier for the challenge.
        name: Name of the challenge.
        description: Description of the challenge.
        criteria: Criteria for completing the challenge.
        reward_points: Reputation points awarded upon completion.
        active: Whether the challenge is currently active.
    """
    __tablename__ = 'challenge'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    criteria = db.Column(db.Text, nullable=False)
    reward_points = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)


class UserChallenge(db.Model):
    """
    UserChallenge model for tracking user progress on challenges.

    Attributes:
        id: Unique identifier.
        user_id: Foreign key to the user.
        challenge_id: Foreign key to the challenge.
        progress: Current progress towards completion.
        completed_at: When the challenge was completed (nullable).
        user: The associated user.
        challenge: The associated challenge.
    """
    __tablename__ = 'user_challenge'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref='challenges')
    challenge = db.relationship('Challenge', backref='users')


class Geofence(db.Model):
    """
    Geofence model for user-defined geographic notification areas.

    Attributes:
        id: Unique identifier for the geofence.
        user_id: Foreign key to the user who created the geofence.
        name: Name of the geofence.
        geometry: GeoJSON geometry (polygon) defining the area.
        notify_on_issue: Whether to notify when issues are reported in this area.
        user: The user who owns the geofence.
    """
    __tablename__ = 'geofence'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    geometry = db.Column(JSON, nullable=False)  # GeoJSON geometry
    notify_on_issue = db.Column(db.Boolean, default=True)
    user = db.relationship('User', backref='geofences')


class UserBehavior(db.Model):
    """
    UserBehavior model for tracking user behavior patterns for rate limiting.

    Attributes:
        id: Unique identifier.
        user_id: Foreign key to the user (nullable for anonymous users).
        ip_address: IP address of the request.
        endpoint: The endpoint accessed.
        method: HTTP method used.
        timestamp: When the request was made.
        status_code: HTTP response status code.
        user_agent: User agent string.
        suspicious_score: Score indicating suspicious behavior (0-100).
        user: The associated user (if authenticated).
    """
    __tablename__ = 'user_behavior'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 addresses can be up to 45 chars
    endpoint = db.Column(db.String(256), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    user_agent = db.Column(db.Text)
    suspicious_score = db.Column(db.Integer, default=0)  # 0-100 scale
    user = db.relationship('User', backref='behaviors')