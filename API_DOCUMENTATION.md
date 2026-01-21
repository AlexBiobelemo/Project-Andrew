# CommunityWatch API Documentation

## Overview

CommunityWatch provides a RESTful API for programmatic access to community issue reporting and management functionality. The API supports versioned endpoints with JSON responses.

## Base URL

```
https://your-domain.com/api/v1/
```

## Authentication

Most API endpoints require authentication. Include the session cookie or use API keys for authenticated requests.

## Rate Limiting

API endpoints are rate-limited. See the main documentation for specific limits.

## Endpoints

### Issues

#### GET /api/v1/issues

Retrieve a list of issues with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (`Reported`, `In Progress`, `Resolved`)
- `category` (optional): Filter by category (see Issue.VALID_CATEGORIES)
- `limit` (optional): Number of results to return (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "issues": [
    {
      "id": 1,
      "category": "Pothole",
      "description": "Large pothole on Main St",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "location_text": "Main St near 5th Ave",
      "status": "Reported",
      "upvote_count": 5,
      "timestamp": "2023-10-01T12:00:00",
      "reporter": {
        "id": 1,
        "username": "johndoe"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/v1/issues/{issue_id}

Retrieve details for a specific issue.

**Response:**
```json
{
  "id": 1,
  "category": "Pothole",
  "description": "Large pothole on Main St",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "location_text": "Main St near 5th Ave",
  "status": "Reported",
  "upvote_count": 5,
  "timestamp": "2023-10-01T12:00:00",
  "resolved_at": null,
  "reporter": {
    "id": 1,
    "username": "johndoe"
  }
}
```

### User Profile

#### GET /api/v1/user/profile

Get current user's profile information.

**Response:**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "reputation_points": 150,
  "role": "user",
  "twofa_enabled": false,
  "is_moderator": false,
  "is_admin": false
}
```

### Statistics

#### GET /api/v1/stats

Get community statistics.

**Response:**
```json
{
  "total_users": 100,
  "total_issues": 250,
  "issues_by_status": {
    "Reported": 100,
    "In Progress": 50,
    "Resolved": 100
  },
  "active_users": 75
}
```

## Web Routes

The following routes are available via web interface but can also be accessed programmatically:

### Issue Management

#### POST /report-issue

Report a new issue.

**Form Data:**
- `category` (optional): Issue category
- `description` (required): Issue description
- `location_text` (required): Location description
- `lat` (required): Latitude
- `lng` (required): Longitude
- `geojson` (optional): GeoJSON geometry
- `photo` (optional): Image file

#### POST /upvote/{issue_id}

Upvote an issue.

#### POST /issue/{issue_id}/update_status

Update issue status (moderator only).

**Form Data:**
- `status`: New status (`Reported`, `In Progress`, `Resolved`)

### User Management

#### POST /register

Register a new user.

**Form Data:**
- `username` (required)
- `email` (required)
- `password` (required)
- `password2` (required)
- `data_processing_consent` (required)
- `marketing_consent` (optional)

#### POST /login

Authenticate user.

**Form Data:**
- `username` (required)
- `password` (required)
- `remember_me` (optional)

### Search and Analytics

#### GET /search

Search for issues.

**Query Parameters:**
- `q`: Search query
- `loc` (optional): Location filter

#### GET /analytics

Get community analytics dashboard.

#### GET /predictive-analytics

Get predictive analytics for issue hotspots.

### Utility

#### POST /reverse-geocode

Convert coordinates to address.

**JSON Payload:**
```json
{
  "lat": 40.7128,
  "lng": -74.0060
}
```

**Response:**
```json
{
  "address": "New York, NY, USA"
}
```

#### POST /check-duplicates

Check for duplicate issues.

**JSON Payload:**
```json
{
  "description": "Pothole on Main St",
  "lat": 40.7128,
  "lng": -74.0060
}
```

**Response:**
```json
{
  "is_duplicate": false
}
```

#### POST /generate-report

Generate weekly report.

**Response:**
```json
{
  "report": "# Civic Issue Report\\n\\n## Summary\\n..."
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation error)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

Error responses include a JSON object with error details:

```json
{
  "error": "Description of the error"
}
```

## Data Formats

- **Dates**: ISO 8601 format (`YYYY-MM-DDTHH:MM:SS`)
- **Coordinates**: Decimal degrees (latitude: -90 to 90, longitude: -180 to 180)
- **GeoJSON**: Standard GeoJSON format for geometric data

## Versioning

API versions are indicated in the URL path (`/api/v1/`, `/api/v2/`). New versions maintain backward compatibility where possible.