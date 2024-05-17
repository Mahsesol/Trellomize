from datetime import datetime

class Comment:
    def __init__(self, username, content):
        self.username = username
        self.content = content
        self.timestamp = datetime.now()

    def __str__(self):
        return f"{self.username} ({self.timestamp}): {self.content}"