# Trellomize
# Project Management App

This is a project management application built with Python and Flet. It allows users to

## Table of Contents

- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Logging](#logging)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Features

- User Authentication: Sign up, log in, and log out functionality.
- Project Management: Create, view, and manage projects.
- User Management: Admin can manage active and inactive users.
- Secure Password Handling: Passwords are hashed before storing in the database.

## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/project-management-app.git
    cd project-management-app
    ```

2. **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Initialize the database:**
    ```bash
    python initialize_database.py
    ```

5. **Run the application:**
    ```bash
    python app.py
    ```

## Usage

- **Sign Up:** Create a new account by providing a username, email, and password.
- **Log In:** Log in with your username and password.
- **Create Project:** After logging in, create a new project.
- **View Projects:** View projects you are leading or a member of.
- **Manage Users:** Admins can manage active and inactive users.

## File Structure

```plaintext
TerlloMize-app/
│
├── app.py                   # Main application entry point
├── database.py              # Database initialization and handling
├── initialize_database.py   # Script to initialize the database
├── history.py               # History tracking for projects and tasks
├── project.py               # Project management functionality
├── task.py                  # Task management functionality
├── user.py                  # User management functionality
├── README.md                # This readme file
├── requirements.txt         # Python package dependencies
└── logs/
    └── app.log              # Application log file
```

## Logging

Logging is configured to output messages to both a file (`logs/app.log`) and the console. The logging format includes the timestamp, logger name, log level, and message.

## Dependencies

- Python 3.7+
- Flet
- SQLite

Dependencies are listed in the `requirements.txt` file. Install them using `pip`:

```bash
pip install -r requirements.txt
```
