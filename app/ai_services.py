"""
Handles interactions with the Google Gemini API for image analysis, duplicate detection,
report generation, and text embedding.
"""
from __future__ import annotations

import json
from PIL import Image
import google.genai as genai
from flask import current_app


class AIError(Exception):
    """Custom exception for AI service errors."""

    def __init__(self, code: str, message: str, user_message: str = None):
        self.code = code
        self.message = message
        self.user_message = user_message or "An error occurred while processing your request. Please try again."
        super().__init__(self.message)


def _handle_ai_error(e: Exception, operation: str) -> dict:
    """Handle AI errors and return structured error response."""
    error_code = "AI_SERVICE_ERROR"
    if "quota" in str(e).lower():
        error_code = "AI_QUOTA_EXCEEDED"
        user_message = "AI service is temporarily unavailable due to high usage. Please try again later."
    elif "network" in str(e).lower() or "connection" in str(e).lower():
        error_code = "AI_NETWORK_ERROR"
        user_message = "Unable to connect to AI services. Please check your connection and try again."
    elif "invalid" in str(e).lower():
        error_code = "AI_INVALID_INPUT"
        user_message = "The provided input could not be processed. Please ensure your data is valid."
    else:
        user_message = "An unexpected error occurred with AI processing. Please try again."

    current_app.logger.error(f"AI {operation} error: {str(e)}")
    return {
        "error": {
            "code": error_code,
            "message": str(e),
            "user_message": user_message
        }
    }

def _configure_genai():
    """Configure the Gemini API with the API key from the Flask app config."""
    genai.configure(api_key=current_app.config['GEMINI_API_KEY'])

def analyze_issue_image(image_path: str) -> dict:
    """
    Analyze an image of a community issue using Gemini Vision.

    Args:
        image_path: File path to the image to analyze.

    Returns:
        A dictionary with 'category' (from predefined list) and 'severity' (Low, Medium, High),
        or an error message if analysis fails.
    """
    try:
        _configure_genai()
        img = Image.open(image_path)
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        categories = [
            'Blocked Drainage', 'Broken Park Bench', 'Broken Streetlight',
            'Broken Traffic Light', 'Damaged Public Property', 'Faded Road Markings',
            'Fallen Tree', 'Flooding', 'Graffiti', 'Leaking Pipe',
            'Overgrown Vegetation', 'Pothole', 'Power Line Down',
            'Stray Animal Concern', 'Waste Dumping', 'Other'
        ]
        categories_str = ', '.join(f"'{cat}'" for cat in categories)

        prompt = (
            "You are an expert at identifying municipal issues from images. "
            f"Analyze this image and return a single, minified JSON object with two keys: "
            f"'category' (choose one from: {categories_str}), and "
            "'severity' (choose one from: 'Low', 'Medium', 'High'). "
            "Do not provide any other text or explanation."
        )

        response = model.generate_content([prompt, img])
        return json.loads(response.text.strip().replace('```json', '').replace('```', ''))

    except Exception as e:
        return _handle_ai_error(e, "image analysis")

def categorize_issue(description: str, image_path: str = None) -> str:
    """
    Categorize an issue based on description and optional image using AI.

    Args:
        description: Text description of the issue.
        image_path: Optional path to image file.

    Returns:
        The predicted category as a string, or 'Other' if categorization fails.
    """
    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        categories = [
            'Blocked Drainage', 'Broken Park Bench', 'Broken Streetlight',
            'Broken Traffic Light', 'Damaged Public Property', 'Faded Road Markings',
            'Fallen Tree', 'Flooding', 'Graffiti', 'Leaking Pipe',
            'Overgrown Vegetation', 'Pothole', 'Power Line Down',
            'Stray Animal Concern', 'Waste Dumping', 'Other'
        ]
        categories_str = ', '.join(f"'{cat}'" for cat in categories)

        prompt = (
            f"Based on the description: '{description}', categorize this municipal issue. "
            f"Choose the most appropriate category from: {categories_str}. "
            "Return only the category name, nothing else."
        )

        content = [prompt]
        if image_path:
            img = Image.open(image_path)
            content.append(img)

        response = model.generate_content(content)
        predicted_category = response.text.strip().replace('```', '').strip()

        # Validate the category
        if predicted_category in categories:
            return predicted_category
        else:
            current_app.logger.warning(f"AI returned invalid category: {predicted_category}")
            return 'Other'

    except Exception as e:
        error_response = _handle_ai_error(e, "categorization")
        current_app.logger.warning(f"AI categorization failed, defaulting to 'Other': {error_response}")
        return 'Other'

def find_duplicate_issue(new_description: str, existing_issues: list) -> dict:
    """
    Use AI to determine if a new issue is a duplicate of existing nearby issues.

    Args:
        new_description: Description of the new issue report.
        existing_issues: List of dictionaries containing nearby issue details.

    Returns:
        A dictionary with 'is_duplicate' (bool) and optional 'duplicate_id' if a duplicate is found.
    """
    if not existing_issues:
        return {'is_duplicate': False}

    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        existing_reports_str = json.dumps(existing_issues, ensure_ascii=False)

        prompt = (
            "You are an issue analysis expert. Based on the text descriptions, determine if the "
            "'new_report' is a duplicate of any 'existing_reports'. Be strict; only identify a "
            "duplicate if it clearly describes the same problem. Return a single, minified JSON "
            "object: {'is_duplicate': true, 'duplicate_id': ID} for duplicates, or "
            "{'is_duplicate': false} if none match.\n\n"
            f"NEW REPORT: {new_description}\n\n"
            f"EXISTING REPORTS: {existing_reports_str}"
        )

        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace('```json', '').replace('```', ''))

    except Exception as e:
        error_response = _handle_ai_error(e, "duplicate detection")
        current_app.logger.warning(f"AI duplicate detection failed, assuming no duplicate: {error_response}")
        return {'is_duplicate': False}

def generate_weekly_report(data_summary: str) -> str:
    """
    Generate a natural language report from structured data using AI.

    Args:
        data_summary: String containing the data to summarize.

    Returns:
        A Markdown-formatted report or an error message if generation fails.
    """
    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        prompt = (
            "You are an analyst for a city council. Based ONLY on the provided data summary, "
            "write a concise, professional briefing in Markdown format. The title MUST be "
            "'Civic Issue Report' followed by the exact 'Date Range' from the data. Highlight "
            "key trends and the most critical issue. Do not add unprovided information.\n\n"
            f"DATA:\n{data_summary}"
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        error_response = _handle_ai_error(e, "report generation")
        return f"Error: {error_response['error']['user_message']}"

def generate_embedding(text_to_embed: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list | None:
    """
    Generate a vector embedding for a block of text.

    Args:
        text_to_embed: Text to create an embedding for.
        task_type: Task type ('RETRIEVAL_DOCUMENT' for storing, 'RETRIEVAL_QUERY' for searching).

    Returns:
        A list of floats representing the vector embedding, or None if an error occurs.
    """
    try:
        _configure_genai()
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text_to_embed,
            task_type=task_type
        )
        return result['embedding']

    except Exception as e:
        _handle_ai_error(e, "embedding generation")
        return None

def predict_issue_hotspots(issues_data: list) -> dict:
    """
    Analyze historical issue data to predict future hotspots and suggest preventive measures.

    Args:
        issues_data: List of dictionaries with issue details (lat, lng, category, timestamp, etc.)

    Returns:
        Dictionary with predicted hotspots and preventive suggestions.
    """
    if not issues_data:
        return {'hotspots': [], 'suggestions': []}

    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        # Prepare data summary
        data_summary = json.dumps(issues_data[:100], ensure_ascii=False)  # Limit to recent 100 for API

        prompt = (
            "You are a data analyst for municipal issue prediction. Based on the provided historical issue data, "
            "predict potential future hotspots for issues. Return a JSON object with: "
            "'hotspots': array of objects with 'lat', 'lng', 'category', 'risk_level' (High/Medium/Low), "
            "'suggestions': array of preventive measure suggestions. "
            "Focus on geographic patterns and category frequencies. "
            "Return only the JSON, no other text."
        )

        response = model.generate_content(f"{prompt}\n\nDATA: {data_summary}")
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))

        return result

    except Exception as e:
        error_response = _handle_ai_error(e, "predictive analytics")
        current_app.logger.warning(f"AI predictive analytics failed, returning empty results: {error_response}")
        return {'hotspots': [], 'suggestions': []}

def moderate_content(text: str, image_path: str = None) -> dict:
    """
    Use AI to check if content is spam or inappropriate.

    Args:
        text: The text content to moderate.
        image_path: Optional path to image file.

    Returns:
        Dictionary with 'is_appropriate' (bool) and 'reason' if inappropriate.
    """
    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        prompt = (
            "You are a content moderator for a community issue reporting platform. "
            "Analyze the following text and determine if it contains spam, inappropriate content, "
            "or is not related to legitimate municipal issues. "
            "Return a JSON object with 'is_appropriate' (boolean) and 'reason' (string, empty if appropriate). "
            "Be strict but fair - allow genuine reports even if poorly written. "
            "Return only the JSON, no other text.\n\n"
            f"TEXT: {text}"
        )

        content = [prompt]
        if image_path:
            img = Image.open(image_path)
            content.append(img)

        response = model.generate_content(content)
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))

        return result

    except Exception as e:
        error_response = _handle_ai_error(e, "content moderation")
        current_app.logger.warning(f"AI content moderation failed, defaulting to allow: {error_response}")
        return {'is_appropriate': True, 'reason': ''}  # Default to allow on error