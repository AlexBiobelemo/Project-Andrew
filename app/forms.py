"""
WTForms definitions for the CommunityWatch application.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
import bleach

from app import db
from app.models import User

# --- NEW: Define and prepare the expanded list of issue categories ---
ISSUE_CATEGORIES = [
    'Blocked Drainage', 'Broken Park Bench', 'Broken Streetlight',
    'Broken Traffic Light', 'Damaged Public Property', 'Faded Road Markings',
    'Fallen Tree', 'Flooding', 'Graffiti', 'Leaking Pipe',
    'Overgrown Vegetation', 'Pothole', 'Power Line Down',
    'Stray Animal Concern', 'Waste Dumping'
]

# Sort categories alphabetically and create the final list of choices, adding 'Other' at the end.
# The format for choices is a list of (value, label) tuples.
category_choices = sorted([(cat, cat) for cat in ISSUE_CATEGORIES]) + [('Other', 'Other')]


def sanitize_html(form, field):
    """
    Sanitize HTML input using bleach to remove potentially malicious content.

    Args:
        form: The WTForms form instance.
        field: The WTForms field instance containing the data to sanitize.

    Returns:
        None: Updates field.data with the sanitized value.
    """
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
    allowed_attributes = {}
    field.data = bleach.clean(field.data, tags=allowed_tags, attributes=allowed_attributes, strip=True)

class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    data_processing_consent = BooleanField('I consent to the processing of my personal data for providing this service', validators=[DataRequired()])
    marketing_consent = BooleanField('I consent to receive marketing communications (optional)')
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Check if username is already taken."""
        user = db.session.scalar(db.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """Check if email is already registered."""
        user = db.session.scalar(db.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# --- UPGRADED IssueForm ---
class IssueForm(FlaskForm):
    """Form for submitting a new issue report with expanded categories."""
    category = SelectField(
        'Category (Optional - will be auto-detected)',
        choices=category_choices,
        validators=[]
    )
    description = TextAreaField(
        'Description',
        validators=[
            DataRequired(message="Please provide a description."),
            Length(max=500),
            sanitize_html
        ]
    )
    photo = FileField(
        'Upload Photo (Optional)',
        validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Only .jpg, .jpeg, and .png images are allowed!')]
    )
    location_text = StringField(
        'Location or Address',
        validators=[
            DataRequired(message="Please provide a location."),
            Length(max=200)
        ]
    )
    # Use HiddenField for data populated by JavaScript (e.g., from a map).
    geojson = HiddenField(validators=[Length(max=1000)])
    submit = SubmitField('Report Issue')

class CommentForm(FlaskForm):
    """Form for submitting a comment on an issue."""
    body = TextAreaField('Comment', validators=[DataRequired(), Length(max=500), sanitize_html])
    submit = SubmitField('Post Comment')

