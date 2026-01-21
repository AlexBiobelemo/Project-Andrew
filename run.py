"""
Entry point for running the CommunityWatch Flask application.
"""

from app import create_app, db
from app.models import User, Issue, Comment, Upvote, Notification, Badge, UserBadge, Challenge, UserChallenge
from sqlalchemy import select

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Provide a shell context for the 'flask shell' command.

    Returns:
        dict: Context with database and model objects for interactive shell access.
    """
    return {
        'db': db,
        'select': select,
        'User': User,
        'Issue': Issue,
        'Comment': Comment,
        'Upvote': Upvote,
        'Notification': Notification
    }

if __name__ == '__main__':
    app.run(debug=True, port=5000)
