Welcome to **CommunityWatch**, a robust and feature-rich Flask-based web application designed to empower communities by providing a platform for reporting, tracking, and managing local issues. Built with a focus on usability, collaboration, and modern web technologies, CommunityWatch leverages an interactive map, real-time notifications, and AI-driven features to create a seamless experience for users and moderators alike. Whether you're a resident looking to improve your neighborhood or a developer interested in contributing to an open-source project, this README will guide you through every aspect of the application.

CommunityWatch is more than just a reporting tool—it's a community hub. Users can report issues with precise geolocation data, visualize them on an interactive map, engage through comments and upvotes, and track progress as moderators address concerns. With advanced features like semantic search, duplicate detection, and a reputation system, CommunityWatch fosters a collaborative environment where community members can actively participate in shaping their surroundings.

This README is designed to be your one-stop resource for understanding, setting up, and contributing to CommunityWatch. We'll cover everything from the application's purpose and features to detailed setup instructions, project architecture, key functionalities, testing procedures, and guidelines for collaboration. Let’s dive in!

---

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
   - [Core Functionality](#core-functionality)
   - [User Experience Enhancements](#user-experience-enhancements)
   - [Advanced Features](#advanced-features)
   - [Security Measures](#security-measures)
3. [Prerequisites](#prerequisites)
   - [Software Requirements](#software-requirements)
   - [Hardware Recommendations](#hardware-recommendations)
4. [Dependencies](#dependencies)
   - [Python Libraries](#python-libraries)
   - [Frontend Frameworks](#frontend-frameworks)
5. [Setup Instructions](#setup-instructions)
   - [Step 1: Clone the Repository](#step-1-clone-the-repository)
   - [Step 2: Set Up a Virtual Environment](#step-2-set-up-a-virtual-environment)
   - [Step 3: Install Dependencies](#step-3-install-dependencies)
   - [Step 4: Configure the Database](#step-4-configure-the-database)
   - [Step 5: Set Environment Variables](#step-5-set-environment-variables)
   - [Step 6: Initialize the Database](#step-6-initialize-the-database)
   - [Step 7: Run the Application](#step-7-run-the-application)
6. [Project Structure](#project-structure)
   - [Directory Overview](#directory-overview)
   - [Key Files and Their Roles](#key-files-and-their-roles)
7. [Key Routes and Functionality](#key-routes-and-functionality)
   - [Homepage (`GET /`)](#homepage-get-)
   - [Issue Reporting (`POST /report-issue`)](#issue-reporting-post-report-issue)
   - [Upvoting (`POST /upvote/<issue_id>`)](#upvoting-post-upvoteissue_id)
   - [Issue Details (`GET/POST /issue/<issue_id>`)](#issue-details-getpost-issueissue_id)
   - [Status Updates (`POST /issue/<issue_id>/update_status`)](#status-updates-post-issueissue_idupdate_status)
   - [User Profiles (`GET /user/<username>`)](#user-profiles-get-userusername)
   - [Analytics Dashboard (`GET /analytics`)](#analytics-dashboard-get-analytics)
   - [Search (`GET /search`)](#search-get-search)
   - [Reverse Geocoding (`POST /reverse-geocode`)](#reverse-geocoding-post-reverse-geocode)
   - [Duplicate Detection (`POST /check-duplicates`)](#duplicate-detection-post-check-duplicates)
   - [Weekly Report Generation (`POST /generate-report`)](#weekly-report-generation-post-generate-report)
8. [Testing the Application](#testing-the-application)
   - [Running in Debug Mode](#running-in-debug-mode)
   - [Testing Core Features](#testing-core-features)
   - [API Testing](#api-testing)
   - [Database Verification](#database-verification)
   - [Security Validation](#security-validation)
9. [Contributing](#contributing)
   - [How to Get Involved](#how-to-get-involved)
   - [Contribution Guidelines](#contribution-guidelines)
   - [Coding Standards](#coding-standards)
10. [License](#license)
11. [Acknowledgements](#acknowledgements)

---

## Introduction

CommunityWatch is an open-source web application built with Flask, a lightweight Python web framework, to address the need for a centralized platform where community members can report and manage local issues. The application was born out of a desire to bridge the gap between residents and local authorities, providing a transparent and interactive way to document and resolve community concerns.

At its heart, CommunityWatch features an interactive map powered by Leaflet.js, allowing users to visualize issues geographically. Whether it’s a broken streetlight, graffiti on a public wall, or an overflowing trash bin, users can report these problems with detailed information, including photos and precise locations. The platform encourages community engagement through upvotes, comments, and a reputation system, while moderators ensure that reported issues are tracked and resolved efficiently.

The application integrates modern technologies such as AI for duplicate detection and semantic search, SQLAlchemy for robust data management, and Bootstrap for a responsive design. It’s designed to be scalable, secure, and extensible, making it an ideal project for developers looking to contribute to a meaningful cause.

This README will take you through every step of getting CommunityWatch up and running, understanding its architecture, and exploring its vast array of features. By the end, you’ll have a thorough understanding of how to use, customize, and contribute to this community-driven platform.

---

## Features

CommunityWatch is packed with features that cater to both end-users and developers. Below, I've categorized them into core functionality, user experience enhancements, advanced features, and security measures for a comprehensive overview.

### Core Functionality

- **Issue Reporting**: Authenticated users can report issues by selecting from predefined categories (e.g., "Pothole," "Waste Dumping," "Flooding"), adding a description, pinpointing the location on the map, and optionally uploading photos. Geolocation data ensures that issues are accurately placed.
- **Interactive Map**: Built with Leaflet.js, the map displays all reported issues as markers, color-coded by status. Clicking a marker reveals detailed information about the issue.
- **Upvoting System**: Users can upvote issues to indicate their significance, helping prioritize community efforts. Each upvote also contributes to the reporter’s reputation points.
- **Commenting**: Authenticated users can leave comments on issues, encouraging discussion and collaboration on potential solutions or updates.
- **Moderation Tools**: Moderators can update issue statuses (e.g., "Reported," "In Progress," "Resolved"), with automatic notifications sent to the reporter and users who upvoted the issue.

### User Experience Enhancements

- **User Profiles**: Every user has a dedicated profile page displaying their username, reputation points, and a list of issues they’ve reported. This fosters transparency and recognizes active contributors.
- **Analytics Dashboard**: A public dashboard provides real-time insights into community issues, including status breakdowns (e.g., percentage of resolved issues), top-voted issues, and a heatmap highlighting areas with unresolved problems.
- **Real-Time Notifications**: Users receive instant updates when the status of an issue they’ve reported or upvoted changes, keeping them engaged and informed.
- **Reputation System**: Users earn points for reporting issues, receiving upvotes, and having issues resolved, gamifying participation and rewarding dedication.

### Advanced Features

- **Geo-Semantic Search**: A powerful search feature allows users to find issues using keywords (e.g., "pothole near park") and location filters. AI embeddings ensure that results are semantically relevant, even if exact matches aren’t found.
- **AI-Powered Duplicate Detection**: When a new issue is reported, the system analyzes its location and description against existing issues to identify potential duplicates, streamlining moderation efforts.
- **Weekly Reports**: An AI-generated summary report is available, providing statistics, trends, and insights into recent community issues for users and moderators.

### Security Measures

- **CSRF Protection**: Built into all forms and AJAX requests using Flask-WTF, ensuring that submissions are legitimate and secure.
- **Input Sanitization**: User inputs are cleaned with the `bleach` library to prevent cross-site scripting (XSS) attacks, keeping the platform safe.
- **Rate Limiting**: Sensitive endpoints like issue reporting and upvoting are rate-limited (e.g., 10 reports per minute, 20 upvotes per minute) to prevent abuse and ensure fair usage.
- **Secure File Uploads**: Uploaded photos are stored with secure filenames using `werkzeug`, and access is restricted to authorized users.

---

## Prerequisites

Before setting up CommunityWatch, ensure your system meets the following requirements.

### Software Requirements

- **Python 3.8 or Higher**: The application is built with Python and relies on modern language features.
- **PostgreSQL 12+**: A relational database is used to store users, issues, and related data. Ensure the `psql` command-line tool is available.
- **Node.js (Optional)**: Required only if you plan to manage frontend dependencies locally instead of using CDNs (e.g., for Leaflet.js or Bootstrap).
- **Redis (Optional)**: Used for caching analytics data to improve performance, though the application functions without it.
- **Git**: Necessary for cloning the repository and managing version control.
- **pip**: Python’s package manager, typically bundled with Python, for installing dependencies.

### Hardware Recommendations

While CommunityWatch can run on modest hardware, the following specs are recommended for a smooth experience:

- **CPU**: Dual-core processor (e.g., Intel i3 or equivalent).
- **RAM**: 4 GB minimum, 8 GB recommended for development and testing.
- **Storage**: At least 5 GB of free space for the application, database, and uploaded files.
- **Internet**: A stable connection for downloading dependencies and accessing external APIs (e.g., Nominatim for geocoding).

---

## Dependencies

CommunityWatch relies on a mix of Python libraries and frontend frameworks to deliver its functionality.

### Python Libraries

- **`flask`**: The core web framework for routing, templating, and request handling.
- **`flask-wtf`**: Manages forms with built-in CSRF protection and validation.
- **`flask-login`**: Handles user authentication, sessions, and login states.
- **`flask-limiter`**: Implements rate limiting to protect endpoints from overuse.
- **`flask-caching`**: Optional caching for analytics and other performance-heavy routes.
- **`sqlalchemy`**: An ORM for interacting with the PostgreSQL database.
- **`psycopg2-binary`**: The PostgreSQL adapter for SQLAlchemy.
- **`numpy`**: Used for vector calculations in AI features like duplicate detection and semantic search.
- **`bleach`**: Sanitizes user inputs to prevent security vulnerabilities.
- **`werkzeug`**: Provides utilities for secure file uploads and password hashing.

### Frontend Frameworks

- **Leaflet.js**: A lightweight, open-source JavaScript library for rendering interactive maps, loaded via CDN.
- **Bootstrap 5**: A CSS framework for responsive design and pre-styled components, also loaded via CDN.

These dependencies are either installed via `pip` or included in templates via CDN links, keeping setup straightforward.

---

## Setup Instructions

Follow these detailed steps to get CommunityWatch running on your local machine.

### Step 1: Clone the Repository

Start by downloading the source code from the project’s GitHub repository.

```bash
git clone https://github.com/AlexBiobelemo/Project-Andrew-CommunityWatch-/tree/main/Version%202
cd communitywatch
```

This creates a local copy of the project in a directory named `communitywatch`.

### Step 2: Set Up a Virtual Environment

A virtual environment isolates the project’s dependencies from your system-wide Python installation.

```bash
python -m venv .venv
```

Activate the environment:
- **Linux/Mac**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows**:
  ```bash
  .venv\Scripts\activate
  ```

Your terminal prompt should now indicate that the virtual environment is active (e.g., `(.venv)`).

### Step 3: Install Dependencies

Install the required Python libraries using `pip`.

```bash
pip install flask flask-wtf flask-login flask-limiter flask-caching sqlalchemy psycopg2-binary numpy bleach werkzeug
```

This command fetches and installs all necessary packages in your virtual environment.

### Step 4: Configure the Database

CommunityWatch uses PostgreSQL for persistent storage. Set it up as follows:

1. **Install PostgreSQL**: Download and install it from [postgresql.org](https://www.postgresql.org/) if not already present.
2. **Create a Database**:
   ```bash
   psql -U postgres
   CREATE DATABASE communitywatch;
   \q
   ```
3. **Update Configuration**: Edit `app/config.py` with your database details:
   ```python
   class Config:
       SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/communitywatch'
       SQLALCHEMY_TRACK_MODIFICATIONS = False
       SECRET_KEY = 'your-secret-key-here'
       UPLOAD_FOLDER = '/path/to/communitywatch/static/uploads'
   ```

Ensure the `username` and `password` match your PostgreSQL credentials.

### Step 5: Set Environment Variables

Set up environment variables to configure Flask and the application.

- **Linux/Mac**:
  ```bash
  export FLASK_APP=app
  export FLASK_ENV=development
  export SECRET_KEY='your-secret-key'
  export UPLOAD_FOLDER='/path/to/communitywatch/static/uploads'
  ```
- **Windows**:
  ```bash
  set FLASK_APP=app
  set FLASK_ENV=development
  set SECRET_KEY=your-secret-key
  set UPLOAD_FOLDER=\path\to\communitywatch\static\uploads
  ```

Alternatively, create a `.env` file in the project root:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
UPLOAD_FOLDER=/path/to/communitywatch/static/uploads
```

Ensure the `UPLOAD_FOLDER` directory exists and is writable:
```bash
mkdir -p static/uploads
chmod -R 755 static/uploads  # Linux/Mac only
```

### Step 6: Initialize the Database

Set up the database schema using Flask-Migrate.

```bash
flask db init
flask db migrate
flask db upgrade
```

These commands create migration scripts and apply them to your database, setting up tables for users, issues, and more.

### Step 7: Run the Application

Launch the Flask development server.

```bash
flask run
```

Visit `http://localhost:5000` in your browser to see CommunityWatch in action. The homepage will display the interactive map and issue reporting interface.

---

### Key Files and Their Roles

- **`app/__init__.py`**: Initializes the Flask app, configures extensions (e.g., SQLAlchemy, Flask-Login), and sets up the application context.
- **`app/config.py`**: Defines configuration classes with settings like database URI, secret key, and upload folder path.
- **`app/models.py`**: Contains SQLAlchemy models:
  - `User`: Stores user data (username, email, password hash, reputation points).
  - `Issue`: Represents reported issues (category, description, location, status).
  - `Upvote`: Tracks user upvotes on issues.
  - `Comment`: Stores user comments on issues.
  - `Notification`: Manages user notifications.
- **`app/forms.py`**: Defines WTForms classes for registration, login, issue reporting, and commenting, with validation rules.
- **`app/routes.py`**: Implements all application routes and their logic, from rendering templates to handling API requests.
- **`app/utils.py`**: Provides helper functions, such as geocoding (address to coordinates) and reverse geocoding.
- **`app/templates/`**: Jinja2 templates for rendering dynamic HTML pages.
- **`static/uploads/`**: Stores user-uploaded photos, accessible only to authenticated users where applicable.

---

## Key Routes and Functionality

CommunityWatch’s functionality is driven by a set of well-defined routes. Below is an exhaustive list with detailed descriptions.

### Homepage (`GET /`)

- **Purpose**: Displays the main interface with an interactive map showing all reported issues.
- **Features**: Users can browse issues, click markers for details, and access the reporting modal (authenticated users only).
- **Implementation**: Renders `index.html` with Leaflet.js integration for the map.

### Issue Reporting (`POST /report-issue`)

- **Purpose**: Allows authenticated users to submit new issues.
- **Parameters**: Category, description, latitude, longitude, optional photo upload.
- **Functionality**: Saves the issue to the database, stores the photo in `uploads`, and updates the map.
- **Rate Limit**: 10 requests per minute per user.

### Upvoting (`POST /upvote/<issue_id>`)

- **Purpose**: Toggles an upvote for a specific issue.
- **Parameters**: `issue_id` in the URL.
- **Functionality**: Updates the issue’s upvote count and the reporter’s reputation points.
- **Rate Limit**: 20 requests per minute per user.

### Issue Details (`GET/POST /issue/<issue_id>`)

- **Purpose**: Displays an issue’s details and allows commenting.
- **GET**: Renders `view_issue.html` with issue info, comments, and upvote button.
- **POST**: Adds a new comment to the issue (authenticated users only).

### Status Updates (`POST /issue/<issue_id>/update_status`)

- **Purpose**: Allows moderators to change an issue’s status.
- **Parameters**: `issue_id`, new status (e.g., "In Progress").
- **Functionality**: Updates the database and sends notifications to the reporter and upvoters.

### User Profiles (`GET /user/<username>`)

- **Purpose**: Shows a user’s public profile.
- **Features**: Displays username, email (if public), reputation points, and a list of reported issues.
- **Implementation**: Renders `user_profile.html`.

### Analytics Dashboard (`GET /analytics`)

- **Purpose**: Provides a public overview of community issues.
- **Features**: Status chart, top-voted issues list, heatmap of unresolved issues.
- **Implementation**: Renders `analytics.html` with cached data (if enabled).

### Search (`GET /search`)

- **Purpose**: Allows users to find issues by keyword and location.
- **Parameters**: `q` (query string), `lat`, `lng` (optional coordinates).
- **Functionality**: Uses AI embeddings for semantic search, renders `search_results.html`.

### Reverse Geocoding (`POST /reverse-geocode`)

- **Purpose**: Converts coordinates to a readable address.
- **Parameters**: JSON payload with `lat` and `lng`.
- **Response**: JSON with address string (e.g., "123 Main St, City").

### Duplicate Detection (`POST /check-duplicates`)

- **Purpose**: Checks for similar existing issues.
- **Parameters**: JSON with issue description and coordinates.
- **Functionality**: Uses AI to compare against nearby issues, returns potential duplicates.

### Weekly Report Generation (`POST /generate-report`)

- **Purpose**: Generates an AI-powered summary of recent issues.
- **Functionality**: Analyzes data from the past week, returns a report with stats and trends.

---

## Testing the Application

To verify that CommunityWatch works as intended, follow these extensive testing procedures.

### Running in Debug Mode

Start the server with debug mode enabled for detailed feedback:

```bash
FLASK_DEBUG=1 flask run
```

### Testing Core Features

- **Homepage**: Load `http://localhost:5000`, ensure the map displays markers, and test the reporting modal (requires login).
- **Issue Reporting**: Log in, report an issue with all fields, and verify it appears on the map and in the database.
- **Upvoting**: Visit an issue page, upvote it, and check the updated count and reputation points.
- **Commenting**: Add a comment to an issue and confirm it’s visible.
- **Profiles**: Check a user’s profile for accurate data.
- **Analytics**: Ensure the dashboard loads with correct stats and visuals.

### API Testing

Use `curl` or Postman to test endpoints:
- **Upvote**:
  ```bash
  curl -X POST -H "X-CSRFToken: <token>" http://localhost:5000/upvote/1
  ```
- **Reverse Geocode**:
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"lat": 37.7749, "lng": -122.4194}' http://localhost:5000/reverse-geocode
  ```

### Database Verification

- Insert test data via the interface and query the database:
  ```sql
  SELECT * FROM issues WHERE status = 'Reported';
  ```
- Verify relationships (e.g., user-to-issue, issue-to-upvotes).

### Security Validation

- Submit forms without CSRF tokens to confirm protection.
- Test rate limits by sending 11 reports in a minute (10 should succeed).

---

## Contributing

CommunityWatch thrives on collaboration. Here’s how you can get involved.

### How to Get Involved

- **Report Bugs**: Use GitHub Issues to flag problems.
- **Suggest Features**: Propose ideas via issues or discussions.
- **Submit Code**: Fork the repo, make changes, and open a pull request.
- **Improve Docs**: Enhance this README or other documentation.

### Contribution Guidelines

- Follow the existing code style (PEP 8 for Python).
- Write clear commit messages (e.g., "Add user profile page").
- Include tests for new features where applicable.
- Document your changes in the PR description.

### Coding Standards

- Use 4-space indentation for Python.
- Name variables descriptively (e.g., `issue_description`).
- Comment complex logic for clarity.

---

## License

CommunityWatch is released under the MIT License. See the `LICENSE` file for full details.

---

## Acknowledgements

Thank you to the open-source community, the Flask team, and contributors to Leaflet.js and Bootstrap for making this project possible. Your tools and support have been invaluable.

---


The following are useful scripts to run inside the Flask shell (flask shell) for administrative tasks.
Make a User a Moderator
This script finds a user by their username and sets their is_moderator flag to True.
# First, manually import what you need
from app.models import User
from app import db

# Find the user
user = User.query.filter_by(username='THE_USERNAME_HERE').first()

# If the user is found, update and save the change
if user:
    user.is_moderator = True
    db.session.commit()
    print(f"Success! User '{user.username}' is now a moderator.")
else:
    print("User not found.")

Generate Search Embeddings for All Existing Issues
If you add issues to the database manually or need to regenerate search data, this script will create embeddings for all issues that are missing them.
# First, manually import what you need
import sqlalchemy as sa
from app.models import Issue
from app import db

# Find all issues without an embedding
issues_to_update = db.session.scalars(sa.select(Issue).where(Issue.embedding == None)).all()

# Loop through them and generate the embedding
for issue in issues_to_update:
    print(f"Generating embedding for: '{issue.category}'")
    issue.generate_and_set_embedding()

# Commit all the changes to the database
db.session.commit()

print(f"Updated {len(issues_to_update)} issues with search data!")


Make a User a Moderator

This script finds a user by their username and sets their is_moderator flag to True.
# First, manually import what you need
from app.models import User
from app import db

# Find the user
user = User.query.filter_by(username='THE_USERNAME_HERE').first()

# If the user is found, update and save the change
if user:
    user.is_moderator = True
    db.session.commit()
    print(f"Success! User '{user.username}' is now a moderator.")
else:
    print("User not found.")


Generate Search Embeddings for All Existing Issues

If you add issues to the database manually or need to regenerate search data, this script will create embeddings for all issues that are missing them.

# First, manually import what you need
import sqlalchemy as sa
from app.models import Issue
from app import db

# Find all issues without an embedding
issues_to_update = db.session.scalars(sa.select(Issue).where(Issue.embedding == None)).all()

# Loop through them and generate the embedding
for issue in issues_to_update:
    print(f"Generating embedding for: '{issue.category}'")
    issue.generate_and_set_embedding()

# Commit all the changes to the database
db.session.commit()

print(f"Updated {len(issues_to_update)} issues with search data!")



