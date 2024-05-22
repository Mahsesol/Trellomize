class User:
    def __init__(self, user_id, username, password, email, is_admin=False, is_active=True, projects=None):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.is_admin = is_admin
        self.is_active = is_active
        self.projects = projects if projects is not None else []


   
    def get_id(self):
        return self.user_id

    
    def set_id(self, user_id):
        self.user_id = user_id

  
    def get_username(self):
        return self.username

   
    def set_username(self, username):
        self.username = username

   
    def get_password(self):
        return self.password

    
    def set_password(self, password):
        self.password = password

    
    def get_is_admin(self):
        return self.is_admin

    
    def set_is_admin(self, is_admin):
        self.is_admin = is_admin

    
    def get_is_active(self):
        return self._is_active

    
    def set_is_active(self, is_active):
        self.is_active = is_active

    
    def get_projects(self):
        return self.projects

    
    def set_projects(self, projects):
        self.projects = projects




    def add_project(self, project):
        """Add a project to the user's project list."""
        self.projects.append(project)

    def remove_project(self, project):
        """Remove a project from the user's project list."""
        if project in self.projects:
            self.projects.remove(project)

    # def get_id(self):
    #     return self.user_id

    # def get_projects(self):
    #     """Return the list of user's projects."""
    #     return self.projects

    def __repr__(self):
        """Return a string representation of the user."""
        return f"User(user_id={self.user_id}, username='{self.username}', is_admin={self.is_admin}, is_active={self.is_active})"

    def to_dict(self):
        """Return a dictionary representation of the user."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "projects": [project.project_id for project in self.projects]
        }
  
