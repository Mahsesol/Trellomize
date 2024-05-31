# Trellomize
## Project Management App
![image](https://github.com/Mahsesol/Trellomize/assets/154425249/97bf4f71-b371-4576-bc77-fa10bd8bf013)

Welcome to Treelomize, a comprehensive project management application designed to streamline your workflow and enhance team collaboration. This app is built with the Flet framework, providing a modern and intuitive user interface.

## Features

### User Authentication
- **Login**: Securely log in to access your projects.
- **Sign Up**: Create a new account to start using Treelomize.
- **Secure Password Handling**: Passwords are hashed before storing in the database.

### Project Management
- **Create Project**: Start new projects with ease.
- **Project List**: View and manage all your projects in one place.
- **Project Details**: Dive into specific projects to see tasks, members, and progress.

### Task Management
- **Add Task**: Create new tasks and assign them to team members.
- **Task Details**: View and edit task details, including status and priority.
- **Task Comments**: Add and view comments on tasks for better communication.
- **Task History**: Track changes and updates to tasks over time.

### User Management
- **Manage Users**: Administer user roles and access within the app.
- **Active/Inactive Users**: View and manage user activity status.

### Theming
- **Light and Dark Themes**: Switch between light and dark themes to suit your preference. The themes are designed with accessibility in mind, ensuring good contrast and readability.


## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Mahsesol/Trellomize.git
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

```
TerlloMize-app/
│
├── main.py                  # Main application entry point
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

## Project Files Overview

### 1. database.db

-  SQLite database file storing project-related information.

### 2. user.py

-  Python module containing classes and functions related to user management.

### 3. test.py

-  Python script for testing functionalities implemented in the project.

### 4. task.py

-  Python module containing classes and functions related to task management.

### 5. project.py

-  Python module containing classes and functions related to project management.

### 6. manager.py

-  Python module containing classes and functions related to project managers.

### 7. history.py

-  Python module containing classes and functions related to project history.

### 8. comment.py

-  Python module containing classes and functions related to comments on tasks or projects.

### 9. main.py

-  Main Python script for running the Treelomize application.

### 10. .gitignore

-  Git configuration file specifying files and directories to be ignored by version control.

### 11. requirement.txt

-  Text file listing Python dependencies required by the project.

### SQL Usage

-  The project utilizes SQL (Structured Query Language) for storing and retrieving information from the SQLite database (`database.db`). SQL queries are used within the project code to interact with the database and manage project-related data.

## Dependencies

- Python 3.7+
- Flet
- SQLite

Dependencies are listed in the `requirements.txt` file. Install them using `pip`:

```bash
pip install -r requirements.txt
```
