"""
Marshmallow schemas for input validation in CommunityWatch.
"""

from marshmallow import Schema, fields, validates, ValidationError, validates_schema
import re
from app.models import Issue


class UserRegistrationSchema(Schema):
    """Schema for user registration validation."""
    username = fields.Str(required=True, validate=[
        fields.validate.Length(min=3, max=64),
        fields.validate.Regexp(r'^[a-zA-Z0-9_]+$', error='Username must contain only letters, numbers, and underscores')
    ])
    email = fields.Email(required=True, validate=fields.validate.Length(max=120))
    password = fields.Str(required=True, validate=fields.validate.Length(min=8))
    password2 = fields.Str(required=True)
    data_processing_consent = fields.Bool(required=True, validate=fields.validate.Equal(True,
        error='Data processing consent is required'))
    marketing_consent = fields.Bool()

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that passwords match."""
        if data['password'] != data['password2']:
            raise ValidationError('Passwords must match', field_name='password2')

    @validates('password')
    def validate_password_strength(self, value):
        """Validate password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError('Password must contain at least one special character')


class UserLoginSchema(Schema):
    """Schema for user login validation."""
    username = fields.Str(required=True, validate=fields.validate.Length(min=1, max=64))
    password = fields.Str(required=True, validate=fields.validate.Length(min=1))
    remember_me = fields.Bool()


class IssueReportSchema(Schema):
    """Schema for issue reporting validation."""
    category = fields.Str(validate=fields.validate.OneOf(Issue.VALID_CATEGORIES + ['']))
    description = fields.Str(required=True, validate=[
        fields.validate.Length(min=10, max=500),
        fields.validate.Regexp(r'^[a-zA-Z0-9\s.,!?-]+$', error='Description contains invalid characters')
    ])
    location_text = fields.Str(required=True, validate=fields.validate.Length(min=1, max=200))
    lat = fields.Float(required=True, validate=fields.validate.Range(min=-90, max=90))
    lng = fields.Float(required=True, validate=fields.validate.Range(min=-180, max=180))
    geojson = fields.Str(validate=fields.validate.Length(max=1000))

    @validates('description')
    def validate_description_content(self, value):
        """Validate description doesn't contain harmful content."""
        harmful_patterns = [
            r'<script', r'javascript:', r'on\w+\s*=', r'eval\s*\(',
            r'document\.cookie', r'window\.location'
        ]
        for pattern in harmful_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError('Description contains potentially harmful content')


class CommentSchema(Schema):
    """Schema for comment validation."""
    body = fields.Str(required=True, validate=[
        fields.validate.Length(min=1, max=500),
        fields.validate.Regexp(r'^[a-zA-Z0-9\s.,!?-]+$', error='Comment contains invalid characters')
    ])


class GeofenceSchema(Schema):
    """Schema for geofence creation validation."""
    name = fields.Str(required=True, validate=fields.validate.Length(min=1, max=128))
    geometry = fields.Dict(required=True)  # GeoJSON geometry
    notify_on_issue = fields.Bool()

    @validates('geometry')
    def validate_geometry(self, value):
        """Validate GeoJSON geometry structure."""
        if not isinstance(value, dict):
            raise ValidationError('Geometry must be a valid GeoJSON object')

        if value.get('type') not in ['Polygon', 'MultiPolygon']:
            raise ValidationError('Geometry must be a Polygon or MultiPolygon')

        coordinates = value.get('coordinates')
        if not coordinates or not isinstance(coordinates, list):
            raise ValidationError('Geometry must contain coordinates')


class IssueUpdateSchema(Schema):
    """Schema for issue status updates (moderator only)."""
    status = fields.Str(required=True, validate=fields.validate.OneOf([
        'Reported', 'In Progress', 'Resolved'
    ]))


class PasswordChangeSchema(Schema):
    """Schema for password change validation."""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=fields.validate.Length(min=8))
    confirm_password = fields.Str(required=True)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new passwords match."""
        if data['new_password'] != data['confirm_password']:
            raise ValidationError('New passwords must match', field_name='confirm_password')

    @validates('new_password')
    def validate_new_password_strength(self, value):
        """Validate new password strength."""
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValidationError('Password must contain at least one digit')


class APIIssuesQuerySchema(Schema):
    """Schema for API issues query parameters."""
    status = fields.Str(validate=fields.validate.OneOf(['Reported', 'In Progress', 'Resolved']))
    category = fields.Str(validate=fields.validate.OneOf(Issue.VALID_CATEGORIES))
    limit = fields.Int(validate=fields.validate.Range(min=1, max=100), missing=50)
    offset = fields.Int(validate=fields.validate.Range(min=0), missing=0)


# Schema instances for reuse
user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
issue_report_schema = IssueReportSchema()
comment_schema = CommentSchema()
geofence_schema = GeofenceSchema()
issue_update_schema = IssueUpdateSchema()
password_change_schema = PasswordChangeSchema()
api_issues_query_schema = APIIssuesQuerySchema()