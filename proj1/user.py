class User:
    def __init__(self, user_id, username, password, is_admin=False, is_active=True):
        self.user_id = user_id  # Unique identifier for the user
        self.username = username  # Username for login
        self.password = password  # User password (in a real app, store hashed passwords)
        self.is_admin = is_admin  # Boolean indicating if the user is an admin
        self.is_active = is_active  # Boolean indicating if the user is active
        self.projects = []  # List to hold user's projects, empty by default

    def add_project(self, project):
        """Add a project to the user's project list."""
        self.projects.append(project)

    def remove_project(self, project):
        """Remove a project from the user's project list."""
        if project in self.projects:
            self.projects.remove(project)

    def get_projects(self):
        """Return the list of user's projects."""
        return self.projects

    def __repr__(self):
        """Return a string representation of the user."""
        return f"User(user_id={self.user_id}, username='{self.username}', is_admin={self.is_admin}, is_active={self.is_active})"


    # Add more user-related methods here
