"""
Machine learning-based issue prioritization for CommunityWatch.
"""

import pickle
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
from flask import current_app
from app import db
from app.models import Issue
from app.utils import calculate_location_density

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'priority_model.pkl')
ENCODER_PATH = os.path.join(os.path.dirname(__file__), 'category_encoder.pkl')

def prepare_training_data():
    """
    Prepare training data from resolved issues.

    Returns:
        X: Feature matrix
        y: Target vector (resolution time in days)
    """
    resolved_issues = Issue.query.filter(Issue.status == 'Resolved', Issue.resolved_at.isnot(None)).all()
    if not resolved_issues:
        return None, None

    X = []
    y = []
    for issue in resolved_issues:
        resolution_time = (issue.resolved_at - issue.timestamp).total_seconds() / (60 * 60 * 24)  # days
        if resolution_time <= 0:
            continue
        location_density = calculate_location_density(issue.latitude, issue.longitude)
        X.append([issue.upvote_count, location_density, issue.category])
        y.append(resolution_time)

    return X, y

def train_priority_model():
    """
    Train the priority model using resolved issues.
    """
    X, y = prepare_training_data()
    if X is None or len(X) < 10:  # Need minimum data
        current_app.logger.warning("Not enough training data for priority model")
        return

    # Encode categories
    categories = [row[2] for row in X]
    encoder = LabelEncoder()
    encoded_categories = encoder.fit_transform(categories)

    # Prepare features
    features = [[row[0], row[1], cat] for row, cat in zip(X, encoded_categories)]

    X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    current_app.logger.info(f"Priority model MSE: {mse}")

    # Save model and encoder
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(encoder, f)

def predict_priority_score(upvotes: int, location_density: int, category: str) -> float:
    """
    Predict priority score for an issue.

    Args:
        upvotes: Number of upvotes
        location_density: Number of issues in vicinity
        category: Issue category

    Returns:
        Priority score (higher is more priority)
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        # Fallback: simple heuristic
        return upvotes * 0.1 + location_density * 0.05

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(ENCODER_PATH, 'rb') as f:
        encoder = pickle.load(f)

    try:
        encoded_cat = encoder.transform([category])[0]
        features = [[upvotes, location_density, encoded_cat]]
        predicted_days = model.predict(features)[0]
        # Priority score: inverse of predicted days, normalized
        score = 1 / (1 + predicted_days)  # Between 0 and 1
        return score
    except Exception as e:
        current_app.logger.error(f"Error predicting priority: {e}")
        return upvotes * 0.1 + location_density * 0.05

def update_issue_priorities():
    """
    Update priority scores for all unresolved issues.
    """
    unresolved_issues = Issue.query.filter(Issue.status != 'Resolved').all()
    for issue in unresolved_issues:
        location_density = calculate_location_density(issue.latitude, issue.longitude)
        score = predict_priority_score(issue.upvote_count, location_density, issue.category)
        issue.priority_score = score
    db.session.commit()