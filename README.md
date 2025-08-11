# Master of Jokes

## Overview

This web application is a platform for users to share, view, rate, and manage jokes. It incorporates user authentication, role-based access control, joke submission limits, and moderation capabilities. The system encourages engagement by limiting joke views based on a "joke balance" and allows moderators to oversee users and content.

---

## Features

### User Roles

- **User**: Can register, login, submit jokes, view others’ jokes, rate jokes, edit or delete their own jokes.
- **Moderator**: Elevated privileges to manage users, edit/delete any joke, toggle debug logging, and oversee platform content.

### Authentication & Authorization

- Secure registration and login with hashed passwords.
- Sessions track user authentication status and roles.
- Access control enforced via decorators (`login_required`, `role_required`, `moderator_required`).

### Joke Management

- Users can leave jokes with constraints on title length (max 10 words) and joke body length (max 100 words).
- Users start with a joke balance, which increments when they leave a joke.
- Viewing jokes from other users consumes one joke balance point.
- Users can rate jokes; ratings average to update joke score.
- Users can edit or delete only their own jokes, unless they are moderators who have broader permissions.

### Moderation Panel

- Moderators can:
  - View the user list with details like email, nickname, joke balance, and role.
  - Edit user joke balances and roles.
  - Promote or demote users to or from moderators.
  - Ensure the last moderator cannot remove themselves.
  - Toggle debug logging on/off dynamically.

### Logging

- Comprehensive logging of user actions, warnings, errors, and system events.
- Logs stored in rotating files with backup and console output.
- Debug mode can be toggled via CLI or moderation panel.

---

## Technology Stack

- **Backend**: Python, Flask Framework
- **Database**: SQLite with schema managed via SQL scripts
- **Templating**: Jinja2 (Flask default)
- **Security**: Password hashing via Werkzeug, session-based authentication
- **CLI Management**: Flask CLI commands for DB initialization and moderator setup

---

## Installation and Setup

### Prerequisites

- Python 3.x
- SQLite
- Recommended: virtual environment for Python packages

### Steps

1. **Clone the repository**

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**

   ```bash
   flask init-db
   ```

4. **Create a default moderator**

  ```bash
   pip install -r requirements.txt
  ```

Use the CLI to add a moderator for administrative access:

5. **Run the application**

  ```bash
  flask run
  ```

## Application Structure


### Blueprints

- `auth`: Handles user registration, login, logout, and session management.
- `jokes`: All joke-related routes including submission, viewing, rating, editing, and deleting.
- `moderation`: Moderator-specific routes for user and app management.

### Database

Two main tables:

- `user`: Stores user credentials, role, and joke balance.
- `joke`: Stores jokes linked to users, with title, body, rating, and timestamps.

Refer to `schema.sql` for details.

---

## Usage

### User Actions

- **Register**: Create an account with email, nickname, and password.
- **Login**: Authenticate with nickname or email.
- **Leave a Joke**: Submit a new joke adhering to title and body length rules.
- **View Jokes**: View jokes submitted by other users, consuming joke balance points.
- **Rate Jokes**: Submit ratings to jokes, influencing their average rating.
- **Edit/Delete Own Jokes**: Modify or remove your own submissions.
- **View Own Jokes**: See a list of jokes you have submitted along with ratings.

### Moderator Actions

- **Manage Users**: View, edit joke balances and roles of all users.
- **Promote/Demote Users**: Toggle user roles between "User" and "Moderator".
- **Edit/Delete Any Joke**: Moderators can edit or delete any joke.
- **Toggle Debug Logging**: Enable or disable detailed debug logs dynamically.

---

## Security and Validation

- Passwords are securely hashed using Werkzeug’s `generate_password_hash`.
- Unique constraints on user emails and nicknames to prevent duplicates.
- Role-based access control prevents unauthorized access to moderation and joke management features.
- Input validation enforces word limits on joke titles and bodies.
- Session management ensures only logged-in users access protected routes.
- Prevents moderators from removing themselves if they are the last moderator.

---

## Logging

- Logs are saved to `logs/app.log` with rotation (max 10MB per file, 5 backups).
- Log entries include timestamps, module names, log levels, and messages.
- Different log levels for file and console output to reduce noise.
- Debug logging can be toggled for detailed traceability.

---

## Development and Maintenance

- Use the Flask CLI commands for database setup and moderator creation.
- Logging configuration is centralized in the app initialization.
- Database connections are managed per-request with teardown.
- Blueprints modularize the application for maintainability and scalability.

---

## Screenshots

*Add screenshots here from the `/screenshots` folder to illustrate:*

- User registration and login pages
- Joke submission form
- Joke listing and viewing pages
- Joke rating interface
- Moderator user management dashboard
- Debug logging toggle interface

---


