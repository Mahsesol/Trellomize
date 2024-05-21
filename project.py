class Project:
    def __init__(self, project_id, project_name, leader_id, members=None):
        self.project_id = project_id
        self.project_name = project_name
        self.leader_id = leader_id
        self.members = members if members is not None else []
        self.tasks = []


   
    def get_project_id(self):
        return self.project_id

    
    def set_project_id(self, project_id):
        self.project_id = project_id

    
    def get_project_name(self):
        return self.project_name

    
    def set_project_name(self, project_name):
        self.project_name = project_name

    
    def get_leader_id(self):
        return self.leader_id

    
    def set_leader_id(self, leader_id):
        self.leader_id = leader_id

    
    def get_members(self):
        return self.members

    
    def set_members(self, members):
        self.members = members

    def add_member(self, member):
        self.members.append(member)

    def remove_member(self, member):
        if member in self.members:
            self.members.remove(member)

    def get_leader_id(self):
        return self.leader_id

    def add_task(self, task):
        self.tasks.append(task)

    def delete_project(self):
        # Logic to delete the project
        pass

    def __str__(self):
        return f"Project ID: {self.project_id}\nTitle: {self.title}\nLeader: {self.leader}"


