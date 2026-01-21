# AI Services Integration Guide

This document details the AI-powered features in CommunityWatch, including Google Gemini integration, machine learning models, and AI-driven functionality.

## Table of Contents

1. [AI Overview](#ai-overview)
2. [Google Gemini Integration](#google-gemini-integration)
3. [AI-Powered Features](#ai-powered-features)
4. [Machine Learning Models](#machine-learning-models)
5. [API Usage and Limits](#api-usage-and-limits)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Cost Management](#cost-management)
9. [Future Enhancements](#future-enhancements)

## AI Overview

CommunityWatch leverages artificial intelligence to enhance user experience and automate moderation tasks. The AI system provides:

- **Content Analysis**: Automatic categorization and moderation of issues
- **Duplicate Detection**: Identifying similar reported issues
- **Semantic Search**: Natural language search capabilities
- **Predictive Analytics**: Forecasting issue hotspots
- **Automated Moderation**: Content appropriateness checking

### Architecture

```
User Input -> AI Processing -> Validation -> Database Storage
                      |
                      v
               Gemini API -> Response Processing -> Feature Integration
```

## Google Gemini Integration

### Setup and Configuration

#### API Key Configuration

```python
# config.py
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
```

#### Initialization

```python
# app/ai_services.py
import google.genai as genai

def _configure_genai():
    """Configure Gemini API with credentials."""
    genai.configure(api_key=current_app.config['GEMINI_API_KEY'])
```

### Model Selection

CommunityWatch uses `gemini-1.5-flash` for optimal balance of speed and accuracy:

```python
model = genai.GenerativeModel(model_name="gemini-1.5-flash")
```

### Prompt Engineering

#### Issue Categorization Prompt

```python
categories = [
    'Blocked Drainage', 'Broken Park Bench', 'Broken Streetlight',
    'Broken Traffic Light', 'Damaged Public Property', 'Faded Road Markings',
    'Fallen Tree', 'Flooding', 'Graffiti', 'Leaking Pipe',
    'Overgrown Vegetation', 'Pothole', 'Power Line Down',
    'Stray Animal Concern', 'Waste Dumping', 'Other'
]

prompt = f"""
You are an expert at identifying municipal issues from images and descriptions.
Analyze this issue and return a single category from: {', '.join(categories)}

Return only the category name, nothing else.
"""
```

## AI-Powered Features

### 1. Issue Categorization

#### Automatic Categorization

When users don't select a category, AI automatically categorizes the issue:

```python
def categorize_issue(description: str, image_path: str = None) -> str:
    """
    Categorize issue based on description and optional image.

    Returns predicted category or 'Other' if categorization fails.
    """
    try:
        _configure_genai()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")

        prompt = f"Based on: '{description}', categorize this municipal issue..."
        content = [prompt]
        if image_path:
            img = Image.open(image_path)
            content.append(img)

        response = model.generate_content(content)
        predicted_category = response.text.strip()

        return predicted_category if predicted_category in VALID_CATEGORIES else 'Other'
    except Exception as e:
        return 'Other'  # Fallback to manual categorization
```

#### Image Analysis

For issues with photos, AI analyzes visual content:

```python
def analyze_issue_image(image_path: str) -> dict:
    """
    Analyze issue image for category and severity.

    Returns: {'category': str, 'severity': 'Low'|'Medium'|'High'}
    """
    img = Image.open(image_path)

    prompt = """
    Analyze this image and return JSON with 'category' and 'severity'.
    Categories: [list of valid categories]
    Severity: Low, Medium, High
    """

    response = model.generate_content([prompt, img])
    return json.loads(response.text)
```

### 2. Duplicate Detection

#### Semantic Similarity

AI compares new issues against existing ones to prevent duplicates:

```python
def find_duplicate_issue(new_description: str, existing_issues: list) -> dict:
    """
    Check if new issue is duplicate of existing issues.

    Args:
        new_description: Description of new issue
        existing_issues: List of existing issue dictionaries

    Returns:
        {'is_duplicate': bool, 'duplicate_id': int or None}
    """
    existing_text = json.dumps(existing_issues, ensure_ascii=False)

    prompt = f"""
    NEW REPORT: {new_description}
    EXISTING REPORTS: {existing_text}

    Is the new report a duplicate? Return JSON: {{"is_duplicate": true/false, "duplicate_id": ID}}
    """

    response = model.generate_content(prompt)
    return json.loads(response.text)
```

### 3. Semantic Search

#### Vector Embeddings

Issues are converted to vector embeddings for semantic search:

```python
def generate_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list:
    """
    Generate vector embedding for text.

    Args:
        text: Text to embed
        task_type: 'RETRIEVAL_DOCUMENT' for storage, 'RETRIEVAL_QUERY' for search

    Returns:
        List of floats representing the embedding vector
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type=task_type
    )
    return result['embedding']
```

#### Similarity Search

```python
def cosine_similarity(v1: list, v2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Search implementation
query_embedding = generate_embedding(query, task_type='RETRIEVAL_QUERY')
similarities = {
    issue.id: cosine_similarity(query_embedding, issue.embedding)
    for issue in issues if issue.embedding
}
```

### 4. Content Moderation

#### Automated Moderation

AI checks content for appropriateness:

```python
def moderate_content(text: str, image_path: str = None) -> dict:
    """
    Check if content is appropriate.

    Returns: {'is_appropriate': bool, 'reason': str}
    """
    prompt = f"""
    Analyze this content for spam or inappropriate material.
    Return JSON: {{"is_appropriate": true/false, "reason": "explanation"}}
    TEXT: {text}
    """

    content = [prompt]
    if image_path:
        content.append(Image.open(image_path))

    response = model.generate_content(content)
    return json.loads(response.text)
```

### 5. Predictive Analytics

#### Hotspot Prediction

AI analyzes historical data to predict future issue hotspots:

```python
def predict_issue_hotspots(issues_data: list) -> dict:
    """
    Predict future issue hotspots from historical data.

    Args:
        issues_data: List of issue dictionaries with lat/lng, category, timestamp

    Returns:
        {'hotspots': list, 'suggestions': list}
    """
    data_summary = json.dumps(issues_data[:100])  # Limit for API

    prompt = f"""
    Analyze historical issue data and predict future hotspots.
    Return JSON with hotspots and preventive suggestions.
    DATA: {data_summary}
    """

    response = model.generate_content(prompt)
    return json.loads(response.text)
```

### 6. Weekly Reports

#### AI-Generated Summaries

```python
def generate_weekly_report(data_summary: str) -> str:
    """
    Generate natural language report from data summary.

    Args:
        data_summary: Structured data summary string

    Returns:
        Markdown-formatted report
    """
    prompt = f"""
    Generate a professional weekly report from this data summary.
    Format as Markdown with title "Civic Issue Report".
    DATA: {data_summary}
    """

    response = model.generate_content(prompt)
    return response.text
```

## Machine Learning Models

### Embedding Model

- **Model**: `models/text-embedding-004`
- **Dimensions**: 768
- **Task Types**: RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY
- **Use Case**: Semantic search and similarity matching

### Generative Model

- **Model**: `gemini-1.5-flash`
- **Capabilities**: Text generation, image analysis, JSON output
- **Use Cases**: Categorization, moderation, report generation

### Custom Models (Future)

- **Duplicate Detection Model**: Fine-tuned for municipal issues
- **Category Classification**: Specialized for local government categories
- **Sentiment Analysis**: Community feedback analysis

## API Usage and Limits

### Rate Limits

Google Gemini API has usage limits:

- **RPM (Requests per Minute)**: 60 for gemini-1.5-flash
- **RPD (Requests per Day)**: 1,500 for gemini-1.5-flash
- **TPM (Tokens per Minute)**: 1,000,000
- **TPD (Tokens per Day)**: 2,000,000

### Cost Structure

- **gemini-1.5-flash**: $0.0015 per 1,000 characters
- **text-embedding-004**: $0.0001 per 1,000 characters

### Monitoring Usage

```python
# Track API usage (implement in ai_services.py)
api_call_count = 0
api_token_count = 0

def track_api_usage(response):
    global api_call_count, api_token_count
    api_call_count += 1
    # Estimate tokens from response
    api_token_count += len(response.text.split()) * 1.3  # Rough estimate
```

### Quota Management

```python
def check_quota():
    """Check if we're approaching API limits."""
    # Implement quota checking logic
    if api_call_count > 1400:  # 93% of daily limit
        current_app.logger.warning("Approaching Gemini API daily limit")
        return False
    return True
```

## Error Handling

### AI Service Errors

```python
class AIError(Exception):
    """Custom exception for AI service errors."""

    def __init__(self, code: str, message: str, user_message: str = None):
        self.code = code
        self.message = message
        self.user_message = user_message or "AI processing failed"

def _handle_ai_error(e: Exception, operation: str) -> dict:
    """Handle AI errors with appropriate user messages."""
    if "quota" in str(e).lower():
        error_code = "AI_QUOTA_EXCEEDED"
        user_message = "AI service temporarily unavailable due to high usage"
    elif "network" in str(e).lower():
        error_code = "AI_NETWORK_ERROR"
        user_message = "Unable to connect to AI services"
    else:
        error_code = "AI_SERVICE_ERROR"
        user_message = "AI processing failed, please try again"

    current_app.logger.error(f"AI {operation} error: {str(e)}")
    return {
        "error": {
            "code": error_code,
            "message": str(e),
            "user_message": user_message
        }
    }
```

### Fallback Mechanisms

```python
def categorize_issue_with_fallback(description: str, image_path: str = None) -> str:
    """Categorize with fallback to 'Other' if AI fails."""
    try:
        return categorize_issue(description, image_path)
    except AIError:
        current_app.logger.warning("AI categorization failed, using fallback")
        return 'Other'
```

### Graceful Degradation

- **Categorization**: Falls back to user-selected category or 'Other'
- **Search**: Falls back to keyword matching
- **Moderation**: Allows content if AI check fails
- **Reports**: Provides basic statistics if AI generation fails

## Performance Optimization

### Caching AI Results

```python
from app.cache import cache

def cached_categorize_issue(description: str, image_path: str = None) -> str:
    """Cache categorization results to reduce API calls."""
    cache_key = f"categorize:{hash(description)}:{hash(image_path or '')}"

    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    result = categorize_issue(description, image_path)
    cache.set(cache_key, result, timeout=3600)  # Cache for 1 hour
    return result
```

### Batch Processing

```python
def batch_generate_embeddings(texts: list) -> list:
    """Generate embeddings for multiple texts efficiently."""
    # Process in batches to optimize API usage
    batch_size = 10
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        # Process batch
        batch_embeddings = [generate_embedding(text) for text in batch]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings
```

### Async Processing

```python
from concurrent.futures import ThreadPoolExecutor

def async_ai_processing():
    """Process AI tasks asynchronously to improve response times."""
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit AI tasks for background processing
        futures = [executor.submit(process_ai_task, task) for task in tasks]
        results = [future.result() for future in futures]
    return results
```

## Cost Management

### Usage Monitoring

```python
class AIMonitor:
    def __init__(self):
        self.daily_cost = 0
        self.monthly_cost = 0

    def track_cost(self, operation: str, tokens: int):
        """Track API usage costs."""
        # Calculate cost based on operation and tokens
        if operation == 'embedding':
            cost = (tokens / 1000) * 0.0001
        elif operation == 'generation':
            cost = (tokens / 1000) * 0.0015
        else:
            cost = 0

        self.daily_cost += cost
        self.monthly_cost += cost

        # Alert if approaching budget limits
        if self.daily_cost > 10:  # $10 daily limit
            current_app.logger.warning(f"Daily AI cost limit approached: ${self.daily_cost}")

ai_monitor = AIMonitor()
```

### Cost Optimization Strategies

1. **Caching**: Cache frequent AI responses
2. **Batching**: Process multiple items together
3. **Fallbacks**: Use simpler methods when possible
4. **Limits**: Implement per-user AI usage limits
5. **Monitoring**: Track and alert on cost spikes

### Budget Alerts

```python
def check_budget_limits():
    """Check if AI usage is within budget limits."""
    daily_limit = float(os.environ.get('AI_DAILY_BUDGET', 10.0))
    monthly_limit = float(os.environ.get('AI_MONTHLY_BUDGET', 200.0))

    if ai_monitor.daily_cost > daily_limit * 0.9:
        # Send alert
        send_budget_alert('daily', ai_monitor.daily_cost)

    if ai_monitor.monthly_cost > monthly_limit * 0.9:
        send_budget_alert('monthly', ai_monitor.monthly_cost)
```

## Future Enhancements

### Planned AI Features

1. **Advanced Image Analysis**
   - Object detection for issue identification
   - Damage severity assessment
   - Before/after comparison

2. **Natural Language Processing**
   - Intent recognition for issue reports
   - Automated issue summarization
   - Multi-language support

3. **Predictive Modeling**
   - Time-series analysis for issue patterns
   - Resource allocation recommendations
   - Preventive maintenance suggestions

4. **Machine Learning Models**
   - Custom-trained duplicate detection
   - Category classification fine-tuning
   - Sentiment analysis for community feedback

### Integration Improvements

1. **Model Fine-tuning**
   - Train on municipal issue data
   - Improve accuracy for local context
   - Reduce API dependency

2. **Edge Computing**
   - On-device AI processing
   - Reduced latency and costs
   - Offline capability

3. **Multi-modal AI**
   - Combined text, image, and location analysis
   - Audio issue reporting (future)
   - Video analysis capabilities

### Performance Enhancements

1. **Model Optimization**
   - Quantized models for faster inference
   - Model distillation for smaller footprint
   - GPU acceleration support

2. **Caching Strategies**
   - Semantic caching for similar queries
   - User-specific result caching
   - CDN integration for AI responses

3. **Scalability Improvements**
   - Distributed AI processing
   - Load balancing for AI services
   - Auto-scaling based on demand

This AI services guide provides comprehensive information about CommunityWatch's AI capabilities. The system is designed to be robust, cost-effective, and scalable while providing valuable automation features.