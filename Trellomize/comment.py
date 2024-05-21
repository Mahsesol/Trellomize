from datetime import datetime

class Comment:
    def __init__(self, username, content, timestamp=None):
        self.username = username
        self.content = content
        self.timestamp = timestamp if timestamp else datetime.now()

    def __str__(self):
        return f"{self.username} ({self.timestamp}): {self.content}"
    
    
    def get_username(self):
        return self.username

    
    def set_username(self, username):
        self.username = username

    
    def get_content(self):
        return self.content

    
    def set_content(self, content):
        self.content = content

    
    def get_timestamp(self):
        return self.timestamp

    
    def set_timestamp(self, timestamp):
        self.timestamp = timestamp


    def to_dict(self):
        return {
            "username": self.username,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }