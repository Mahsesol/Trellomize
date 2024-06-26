from enum import Enum
from datetime import datetime, timedelta
import uuid
from comment import Comment

class Priority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    def __lt__(self, other):
        priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        return priority_order.index(self.name) < priority_order.index(other.name)

class Status(Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class Task:
    def __init__(self, project_id, title, task_id=None , description="", priority=Priority.LOW, status=Status.BACKLOG, assignees=None, start_datetime=None, end_datetime=None):
        self.task_id = task_id if task_id else str(uuid.uuid4())  
        self.project_id = project_id
        self.title = title
        self.description = description
        self.start_datetime = start_datetime if start_datetime else datetime.now()
        self.end_datetime = end_datetime if end_datetime else self.start_datetime + timedelta(hours=24)
        self.priority = priority
        self.status = status
        self.assignees = assignees if assignees is not None else []  # List of user IDs
        self.history = []
        self.comments = []
    



    
    def get_task_id(self):
        return self.task_id

    
    def set_task_id(self, task_id):
        self.task_id = task_id

    
    def get_project_id(self):
        return self.project_id

    
    def set_project_id(self, project_id):
        self.project_id = project_id

    
    def get_title(self):
        return self.title

    
    def set_title(self, title):
        self.title = title

    
    def get_description(self):
        return self.description

    
    def set_description(self, description):
        self.description = description

    
    def get_start_datetime(self):
        return self.start_datetime

    
    def set_start_datetime(self, start_datetime):
        self.start_datetime = start_datetime

    
    def get_end_datetime(self):
        return self.end_datetime

    
    def set_end_datetime(self, end_datetime):
        self.end_datetime = end_datetime

    
    def get_priority(self):
        return self.priority

    
    def set_priority(self, priority):
        self.priority = priority

    
    def get_status(self):
        return self.status

    
    def set_status(self, status):
        self.status = status

    
    def get_assignees(self):
        print(self.assignees)
        return self.assignees

   
    def set_assignees(self, assignees):
        self.assignees = assignees

    
    def get_history(self):
        return self.history

    
    def set_history(self, history):
        self.history = history

    
    def get_comments(self):
        return self.comments

    
    def set_comments(self, comments):
        self.comments = comments

    def get_db(self):
       from database import Database
       return Database()

    def assign_user(self, user_id, author):
        if user_id not in self.assignees:
            self.assignees.append(user_id)
            db = self.get_db()
            user = db.get_user_by_id(user_id)
            if user:
                self.add_history(f"Assigned user {user.get_username()}", author)


    def unassign_user(self, user_id, author):
        if user_id not in self.assignees:
            self.assignees.append(user_id)
            db = self.get_db()
            user = db.get_user_by_id(user_id)
            if user:
                self.add_history(f"Unassigned user {user.get_username()}", author)


    def add_history(self, action, author,timestamp=None):
        timestamp = timestamp if timestamp else datetime.now()
        self.history.append(f"{timestamp}: {action}")
        self.add_task_history(action, author)

    def add_comment(self, username, content, timestamp = None):
        comment = Comment(username, content, timestamp)
        self.comments.append(comment)
        if not timestamp :
            self.add_history(f"Added comment by {username}", username)

    def __str__(self):
        return (f"Task ID: {self.task_id}\nTitle: {self.title}\nDescription: {self.description}\n"
                f"Start: {self.start_datetime}\nEnd: {self.end_datetime}\nPriority: {self.priority.name}\n"
                f"Status: {self.status.name}\nAssignees: {', '.join(map(str, self.assignees))}\n"
                f"History: {self.history}\nComments: {[str(comment) for comment in self.comments]}")

    def add_task_history(self, action, author):
        # This function will be implemented in the database class to save the history
        pass



   

    def to_dict(self):
        assignees = ", ".join(map(str, self.assignees))
        comments = [comment.to_dict() for comment in self.comments]
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "start_datetime": self.start_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "end_datetime": self.end_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "priority": self.priority.name,
            "status": self.status.name,
            "assignees": assignees,
            "history": self.history,
            "comments": comments
        }








