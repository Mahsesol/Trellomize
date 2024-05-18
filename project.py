class Project:
    def __init__(self, project_id, title, leader):
        self.project_id = project_id
        self.title = title
        self.leader = leader
        self.members = []
        self.tasks = []  # List to store tasks for the project

    def add_member(self, member):
        self.members.append(member)

    def remove_member(self, member):
        if member in self.members:
            self.members.remove(member)

    def add_task(self, task):
        self.tasks.append(task)

    def delete_project(self):
        # Logic to delete the project
        pass

    def __str__(self):
        return f"Project ID: {self.project_id}\nTitle: {self.title}\nLeader: {self.leader}"


