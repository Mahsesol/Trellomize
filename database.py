import sqlite3
import hashlib
import re
from project import Project
from user import User
from datetime import datetime
import uuid





DB_FILE = 'database.db'

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # Users table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                isadmin BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Projects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                leader_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                FOREIGN KEY (leader_id) REFERENCES users(id)
            )
        """)

        # Project members table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                PRIMARY KEY (project_id, user_id)
            )
        """)

        # Tasks table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Task assignees table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_assignees (
                task_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                PRIMARY KEY (task_id, user_id)
            )
        """)

        # Comments table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY,
                task_id TEXT NOT NULL,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        # Task history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY,
                task_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                author TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        self.conn.commit()

    def add_project(self, project_id, project_name, leader_id, member_ids):
        query = "INSERT INTO projects (id, leader_id, project_name) VALUES (?, ?, ?)"
        self.conn.execute(query, (project_id, leader_id, project_name))

        query = "INSERT INTO project_members (project_id, user_id) VALUES (?, ?)"
        for member_id in member_ids:
            self.conn.execute(query, (project_id, member_id))

        self.conn.commit()

    def add_task(self, task):
        query = """INSERT INTO tasks (id, project_id, title, description, start_datetime, end_datetime, priority, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        self.conn.execute(query, (
            task.task_id, task.project_id, task.title, task.description, task.start_datetime.isoformat(),
            task.end_datetime.isoformat(), task.priority.value, task.status.value))

        query = "INSERT INTO task_assignees (task_id, user_id) VALUES (?, ?)"
        for assignee in task.assignees:
            self.conn.execute(query, (task.task_id, assignee))

        self.conn.commit()

    def get_project_tasks(self, project_id):
        query = "SELECT * FROM tasks WHERE project_id = ?"
        return self.conn.execute(query, (project_id,)).fetchall()

    def add_comment(self, task_id, username, content):
        timestamp = datetime.now().isoformat()
        query = "INSERT INTO comments (task_id, username, content, timestamp) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (task_id, username, content, timestamp))
        self.conn.commit()

    def get_task_comments(self, task_id):
        query = "SELECT * FROM comments WHERE task_id = ?"
        return self.conn.execute(query, (task_id,)).fetchall()

    def add_task_history(self, task_id, action, author):
        timestamp = datetime.now().isoformat()
        query = "INSERT INTO task_history (task_id, action, timestamp, author) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (task_id, action, timestamp, author))
        self.conn.commit()

    def get_task_history(self, task_id):
        query = "SELECT * FROM task_history WHERE task_id = ?"
        return self.conn.execute(query, (task_id,)).fetchall()


    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username, password, email):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, email))
        self.conn.commit()

    def add_admin(self, username, password):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email, isadmin) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, "admin@example.com", True))
        self.conn.commit()

    @staticmethod
    def create_admin(username, password):
        db = Database()
        try:
            db.add_admin(username, password)
            print("Admin created successfully!")
        except sqlite3.IntegrityError:
            print("Admin already exists!")

    def is_admin(self, username):
        query = "SELECT isadmin FROM users WHERE username=?"
        result = self.conn.execute(query, (username,)).fetchone()
        if result and result[0] == 1:
            return True
        return False
    
    def admin_exists(self):
        query = "SELECT * FROM users WHERE isadmin = 1"
        result = self.conn.execute(query).fetchone()
        return result is not None

    def get_user(self, username, password):
        hashed_password = self._hash_password(password)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        return self.conn.execute(query, (username, hashed_password)).fetchone()

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username=?"
        return self.conn.execute(query, (username,)).fetchone()

    def get_all_users(self):
        query = "SELECT * FROM users WHERE username != ?"
        return self.conn.execute(query, ("admin",)).fetchall()

    def get_all_active_users(self):
        query = "SELECT * FROM users WHERE active = 1"
        return self.conn.execute(query).fetchall()

    def inactivate_user(self, user_id):
        query = "UPDATE users SET active = 0 WHERE id = ?"
        self.conn.execute(query, (user_id,))
        self.conn

    def get_project(self, project_id):
        query = "SELECT * FROM projects WHERE id =?"
        return self.conn.execute(query, (project_id,)).fetchone()



# DB_FILE = 'database.db'

# class Database:
#     def __init__(self):
#         self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
#         self.create_tables()

#     def create_tables(self):
#         # Users table
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY,
#                 username TEXT UNIQUE NOT NULL,
#                 password TEXT NOT NULL,
#                 email TEXT UNIQUE NOT NULL,
#                 active BOOLEAN DEFAULT TRUE,
#                 isadmin BOOLEAN DEFAULT FALSE
#             )
#         """)
        
#         # Projects table
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS projects (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER NOT NULL,
#                 project_name TEXT NOT NULL,
#                 FOREIGN KEY (user_id) REFERENCES users(id)
#             )
#         """)
        
#         # Tasks table
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS tasks (
#                 id TEXT PRIMARY KEY,
#                 project_id INTEGER NOT NULL,
#                 title TEXT NOT NULL,
#                 description TEXT,
#                 start_datetime TEXT NOT NULL,
#                 end_datetime TEXT NOT NULL,
#                 priority TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 FOREIGN KEY (project_id) REFERENCES projects(id)
#             )
#         """)

#         # Task Assignees table
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS task_assignees (
#                 task_id TEXT NOT NULL,
#                 user_id INTEGER NOT NULL,
#                 PRIMARY KEY (task_id, user_id),
#                 FOREIGN KEY (task_id) REFERENCES tasks(id),
#                 FOREIGN KEY (user_id) REFERENCES users(id)
#             )
#         """)

#         # Comments table
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS comments (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 task_id TEXT NOT NULL,
#                 username TEXT NOT NULL,
#                 content TEXT NOT NULL,
#                 timestamp TEXT NOT NULL,
#                 FOREIGN KEY (task_id) REFERENCES tasks(id)
#             )
#         """)
        
#         self.conn.commit()

#     def _hash_password(self, password):
#         return hashlib.sha256(password.encode()).hexdigest()

#     def add_user(self, username, password, email):
#         hashed_password = self._hash_password(password)
#         query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
#         self.conn.execute(query, (username, hashed_password, email))
#         self.conn.commit()

#     def add_admin(self, username, password):
#         hashed_password = self._hash_password(password)
#         query = "INSERT INTO users (username, password, email, isadmin) VALUES (?, ?, ?, ?)"
#         self.conn.execute(query, (username, hashed_password, "admin@example.com", True))
#         self.conn.commit()

#     @staticmethod
#     def create_admin(username, password):
#         db = Database()
#         try:
#             db.add_admin(username, password)
#             print("Admin created successfully!")
#         except sqlite3.IntegrityError:
#             print("Admin already exists!")

#     def is_admin(self, username):
#         query = "SELECT isadmin FROM users WHERE username=?"
#         result = self.conn.execute(query, (username,)).fetchone()
#         if result and result[0] == 1:
#             return True
#         return False
    
#     def admin_exists(self):
#         query = "SELECT * FROM users WHERE isadmin = 1"
#         result = self.conn.execute(query).fetchone()
#         return result is not None

#     def get_user(self, username, password):
#         hashed_password = self._hash_password(password)
#         query = "SELECT * FROM users WHERE username=? AND password=?"
#         return self.conn.execute(query, (username, hashed_password)).fetchone()

#     def get_all_users(self):
#         query = "SELECT * FROM users WHERE username != ?"
#         return self.conn.execute(query, ("admin",)).fetchall()

#     def get_all_active_users(self):
#         query = "SELECT * FROM users WHERE active = 1"
#         return self.conn.execute(query).fetchall()

#     def inactivate_user(self, user_id):
#         query = "UPDATE users SET active = 0 WHERE id = ?"
#         self.conn.execute(query, (user_id,))
#         self.conn.commit()

#     def get_all_inactive_users(self):
#         query = "SELECT * FROM users WHERE active = 0"
#         return self.conn.execute(query).fetchall()

#     def activate_user(self, user_id):
#         query = "UPDATE users SET active = 1 WHERE id = ?"
#         self.conn.execute(query, (user_id,))
#         self.conn.commit()

#     def add_project(self, user_id, project_name):
#         query = "INSERT INTO projects (user_id, project_name) VALUES (?, ?)"
#         self.conn.execute(query, (user_id, project_name))
#         self.conn.commit()

#     def get_projects_by_user(self, user_id):
#         query = "SELECT * FROM projects WHERE user_id = ?"
#         return self.conn.execute(query, (user_id,)).fetchall()

#     def add_task(self, project_id, title, description, start_datetime, end_datetime, priority, status):
#         task_id = str(uuid.uuid4())
#         query = """
#             INSERT INTO tasks (id, project_id, title, description, start_datetime, end_datetime, priority, status)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """
#         self.conn.execute(query, (task_id, project_id, title, description, start_datetime, end_datetime, priority, status))
#         self.conn.commit()

#     def get_tasks_by_project(self, project_id):
#         query = "SELECT * FROM tasks WHERE project_id = ?"
#         return self.conn.execute(query, (project_id,)).fetchall()

#     def assign_task(self, task_id, user_id):
#         query = "INSERT INTO task_assignees (task_id, user_id) VALUES (?, ?)"
#         self.conn.execute(query, (task_id, user_id))
#         self.conn.commit()

#     def unassign_task(self, task_id, user_id):
#         query = "DELETE FROM task_assignees WHERE task_id = ? AND user_id = ?"
#         self.conn.execute(query, (task_id, user_id))
#         self.conn.commit()

#     def add_comment(self, task_id, username, content):
#         timestamp = datetime.now().isoformat()
#         query = "INSERT INTO comments (task_id, username, content, timestamp) VALUES (?, ?, ?, ?)"
#         self.conn.execute(query, (task_id, username, content, timestamp))
#         self.conn.commit()

#     def get_comments_by_task(self, task_id):
#         query = "SELECT * FROM comments WHERE task_id = ?"
#         return self.conn.execute(query, (task_id,)).fetchall()







