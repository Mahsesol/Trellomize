from datetime import datetime

class History:
    def __init__(self, action, author, timestamp=None):
        self.action = action
        self.author = author
        self.timestamp = timestamp if timestamp else datetime.now()

    def __str__(self):
        return f"{self.author} ({self.action}): {self.timestamp}"
    
    
    def get_author(self):
        return self.author

    
    def set_author(self, author):
        self.author = author

    
    def get_action(self):
        return self.action

    
    def set_action(self, action):
        self.action = action

    
    def get_timestamp(self):
        return self.timestamp

    
    def set_timestamp(self, timestamp):
        self.timestamp = timestamp