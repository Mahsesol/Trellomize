from enum import Enum
from datetime import datetime, timedelta
import uuid
from comment import Comment

class Priority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Status(Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class Task:
    def __init__(self, project_id, title, description="", priority=Priority.LOW, status=Status.BACKLOG, assignees=None):
        self.task_id = str(uuid.uuid4())  # Generate a unique ID for the task
        self.project_id = project_id
        self.title = title
        self.description = description
        self.start_datetime = datetime.now()
        self.end_datetime = self.start_datetime + timedelta(hours=24)
        self.priority = priority
        self.status = status
        self.assignees = assignees if assignees is not None else []  # List of user IDs
        self.history = []
        self.comments = []

    def assign_user(self, user_id):
        if user_id not in self.assignees:
            self.assignees.append(user_id)
            self.add_history(f"Assigned user {user_id}")

    def unassign_user(self, user_id):
        if user_id in self.assignees:
            self.assignees.remove(user_id)
            self.add_history(f"Unassigned user {user_id}")

    def add_history(self, action, author):
        timestamp = datetime.now()
        self.history.append(f"{timestamp}: {action}")
        self.add_task_history(action, author)

    def add_comment(self, username, content):
        comment = Comment(username, content)
        self.comments.append(comment)
        self.add_history(f"Added comment by {username}", username)

    def __str__(self):
        return (f"Task ID: {self.task_id}\nTitle: {self.title}\nDescription: {self.description}\n"
                f"Start: {self.start_datetime}\nEnd: {self.end_datetime}\nPriority: {self.priority.name}\n"
                f"Status: {self.status.name}\nAssignees: {', '.join(map(str, self.assignees))}\n"
                f"History: {self.history}\nComments: {[str(comment) for comment in self.comments]}")

    def add_task_history(self, action, author):
        # This function will be implemented in the database class to save the history
        pass











