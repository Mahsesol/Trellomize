class Project:
    def __init__(self, name):
        self.name = name
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def get_project_info(self):
        return f"Project Name: {self.name}\nTasks: {', '.join(self.tasks)}"
