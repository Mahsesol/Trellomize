import sqlite3
import hashlib
import re
from project import Project
from user import User
from datetime import datetime
from history import History
import uuid
from flet import *
from task import *
import tempfile
import os







DB_FILE = 'database.db'

class Database:

    def __init__(self, DB_FILE = 'database.db' ):
        self.db_file = DB_FILE
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()



    def create_tables(self):
      
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
        
     
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                leader_id INTEGER NOT NULL,
                project_name TEXT NOT NULL,
                FOREIGN KEY (leader_id) REFERENCES users(id)
            )
        """)

       
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                PRIMARY KEY (project_id, user_id)
            )
        """)

      
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

      
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS task_assignees (
                task_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                PRIMARY KEY (task_id, user_id)
            )
        """)

     
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
        query = "INSERT INTO projects (id, project_name, leader_id) VALUES (?, ?, ?)"
        self.conn.execute(query, (project_id, project_name, leader_id))

        query = "INSERT INTO project_members (project_id, user_id) VALUES (?, ?)"
        for member_id in member_ids:
            self.conn.execute(query, (project_id, member_id))

        self.conn.commit()

    def add_task(self, task):
        query = """INSERT INTO tasks (id, project_id, title, description, start_datetime, end_datetime, priority, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        self.conn.execute(query, (
            task.get_task_id(), task.get_project_id(), task.get_title(), task.get_description(), task.get_start_datetime().strftime('%Y-%m-%d %H:%M:%S.%f')  ,
            task.get_end_datetime().strftime('%Y-%m-%d %H:%M:%S.%f'), task.get_priority(), task.get_status()))

        query = "INSERT INTO task_assignees (task_id, user_id) VALUES (?, ?)"
        for assignee in task.get_assignees():
            self.conn.execute(query, (task.get_task_id(), assignee))

        self.conn.commit()



    def add_comment(self, task_id, username, content):
        timestamp = datetime.now().isoformat()
        query = "INSERT INTO comments (task_id, username, content, timestamp) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (task_id, username, content, timestamp))
        self.conn.commit()

    def get_task_comments(self, task_id):
        query = "SELECT username, content, timestamp FROM comments WHERE task_id = ?"
        results = self.conn.execute(query, (task_id,)).fetchall()
        return [Comment(username=row[0], content=row[1], timestamp=row[2]) for row in results]
    
    def add_task_history(self, task_id, action, author):
        timestamp = datetime.now().isoformat()
        query = "INSERT INTO task_history (task_id, action, timestamp, author) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (task_id, action, timestamp, author))
        self.conn.commit()

    def get_task_history(self, task_id):
        query = "SELECT action, author, timestamp FROM task_history WHERE task_id = ? ORDER BY timestamp ASC"
        results = self.conn.execute(query, (task_id,)).fetchall()
        return [History(author=row[1], action=row[0], timestamp=row[2]) for row in results]


    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # def add_user(self, username, password, email):
    #     hashed_password = self._hash_password(password)
    #     query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
    #     self.conn.execute(query, (username, hashed_password, email))
    #     self.conn.commit()

    def add_user(self, username, password, email, active=1):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email, active) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, email, active))
        self.conn.commit()
    


    def add_admin(self, username, password):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email, isadmin) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, "admin@example.com", True))
        self.conn.commit()

    @staticmethod
    def create_admin(username, password, DB_FILE = 'database.db'  ):
        db = Database(DB_FILE)
        try:
            db.add_admin(username, password)
            # print("Admin created successfully!")
        except sqlite3.IntegrityError:
            # print("Admin already exists!")
            pass

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
    
    def project_id_exist(self,project_id):
        query = "SELECT * FROM projects WHERE id=?"
        result = self.conn.execute(query, (project_id,)).fetchone()
        return result is not None 

    def get_user(self, username, password):
        hashed_password = self._hash_password(password)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        return self.conn.execute(query, (username, hashed_password)).fetchone()

    def get_user_by_username(self, username):
        query = "SELECT * FROM users WHERE username=?"
        result = self.conn.execute(query, (username,)).fetchone()
        projects = self.get_user_project_member(result[0])
        projects.append(self.get_user_project_leader(result[0]))
        if result:
            return User(result[0], result[1], result[2], result[3], result[5], result[4],projects)
        else:
            return None

    def get_all_users(self):
        query = "SELECT * FROM users WHERE username != ?"
        return [User(result[0], result[1], result[2], result[3], result[5], result[4]) for result in self.conn.execute(query,("",)).fetchall()]


    def get_all_active_users(self):
        query = "SELECT * FROM users WHERE active = 1"
        return [User(result[0], result[1], result[2], result[3], result[5], result[4]) for result in self.conn.execute(query).fetchall()]

    def get_all_inactive_users(self):
        query = "SELECT * FROM users WHERE active = 0"
        return [User(result[0], result[1], result[2], result[3], result[5], result[4]) for result in self.conn.execute(query).fetchall()]



    def inactivate_user(self, user_id):
        query = "UPDATE users SET active = 0 WHERE id = ?"
        self.conn.execute(query, (user_id,))
        self.conn.commit()

    def activate_user(self, user_id):
        query = "UPDATE users SET active = 1 WHERE id = ?"
        self.conn.execute(query, (user_id,))
        self.conn.commit()

    def get_project(self, project_id):
        query = "SELECT * FROM projects WHERE id=?"
        result = self.conn.execute(query, (project_id,)).fetchone()
        if result:
            project = Project(result[0], result[2], result[1])
            return project
        else:
            return None
        
    def get_project_member_ids(self, project_id):
       query = "SELECT user_id FROM project_members WHERE project_id=?"
       return [row[0] for row in self.conn.execute(query, (project_id,)).fetchall()]  


    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id=?"
        result = self.conn.execute(query, (user_id,)).fetchone()
        if result:
            return User(result[0], result[1], result[2], result[3], result[5], result[4])
        else:
            return None
    
    def get_project_members(self, project_id):
       query = "SELECT user_id FROM project_members WHERE project_id=?"
       member_ids = [member_id for member_id, in self.conn.execute(query, (project_id,)).fetchall()]

       members = []
       for member_id in member_ids:
          user = self.get_user_by_id(member_id)
          members.append(user)

       return members
    
    def get_current_user_id(self, page):
        username = page.session.get("username")
        user = self.get_user_by_username(username)
        return user.get_id()
    
    def get_current_user_username(self, page):
        username = page.session.get("username")
        # user = self.get_user_by_username(username)
        # return user.get_username()
        return username

    def get_current_user(self, page):
        username = page.session.get("username")
        return self.get_user_by_username(username)
        
    def add_project_member(self, project_id, member_id):
        query = "INSERT INTO project_members (project_id, user_id) VALUES (?, ?) "
        self.conn.execute(query, (project_id, member_id))
        self.conn.commit()
    
    def remove_project_member(self, project_id, member_id):
        query = "DELETE FROM project_members WHERE project_id=? AND user_id=?"
        self.conn.execute(query, (project_id, member_id))
        self.conn.commit()

    def get_task_assignees(self, task_id):
        query = "SELECT user_id FROM task_assignees WHERE task_id=?"
        assignee_ids = [row[0] for row in self.conn.execute(query, (task_id,)).fetchall()]  # Extract user_id from each row
        return assignee_ids


    def get_project_tasks(self, project_id):
        query = "SELECT * FROM tasks WHERE project_id = ?"
        result = self.conn.execute(query, (project_id,)).fetchall()

        tasks = []
        for row in result:
            task_id = row[0]
            project_id = row[1]
            title = row[2]
            description = row[3]
            start_datetime = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f')
            end_datetime = datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S.%f')
            priority = Priority(row[6])
            status = Status(row[7])
            assignees = self.get_task_assignees(task_id)
            task = Task(task_id=task_id, project_id=project_id, title=title, description=description, priority=priority, status=status, assignees=assignees, start_datetime=start_datetime, end_datetime=end_datetime)
            tasks.append(task)

        return tasks
    
    def get_task(self, task_id):
        query = "SELECT * FROM tasks WHERE id=?"
        result = self.conn.execute(query, (task_id,)).fetchone()

        if result:
            project_id = result[1]
            title = result[2]
            description = result[3]
            start_datetime = datetime.strptime(result[4],'%Y-%m-%d %H:%M:%S.%f')
            end_datetime = datetime.strptime(result[5], '%Y-%m-%d %H:%M:%S.%f')
            priority = Priority(result[6])
            status = Status(result[7])
            assignees = self.get_task_assignees(task_id)

            task = Task(task_id=task_id, project_id=project_id, title=title, description=description, priority=priority, status=status, assignees=assignees, start_datetime=start_datetime, end_datetime=end_datetime)
            return task
        else:
            return None
        
    def get_current_user(self, page):
        username = page.session.get("username")
        return self.get_user_by_username(username)
    
    def get_user_project_member(self, user_id):
        query = "SELECT project_id FROM project_members WHERE user_id = ?"
        project_ids = [result[0] for result in self.conn.execute(query, (user_id,)).fetchall()]
        projects = [self.get_project(project_id) for project_id in project_ids]
        return projects
    

    def get_user_project_leader(self, user_id):
        query = "SELECT * FROM projects WHERE leader_id = ?"
        results = self.conn.execute(query, (user_id,)).fetchall()
        projects = [Project(result[0], result[2], result[1]) for result in results]
        return projects
    
    def add_assignee(self, task_id, user_id):
        query = "INSERT INTO task_assignees (task_id, user_id) VALUES (?, ?)"
        self.conn.execute(query, (task_id, user_id))
        self.conn.commit()

    def remove_assignee(self, task_id, user_id):
        query = "DELETE FROM task_assignees WHERE task_id=? AND user_id=?"
        self.conn.execute(query, (task_id, user_id))
        self.conn.commit()

    def change_status(self, task_id, new_status):
        query = "UPDATE tasks SET status=? WHERE id=?"
        self.conn.execute(query, (new_status, task_id))
        self.conn.commit()

    def change_priority(self, task_id, new_priority):
        query = "UPDATE tasks SET priority = ? WHERE id = ?"
        self.conn.execute(query, (new_priority.value, task_id))
        self.conn.commit()

    def purge_data(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM projects")
        cursor.execute("DELETE FROM project_members")
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM task_assignees")
        cursor.execute("DELETE FROM comments")
        cursor.execute("DELETE FROM task_history")
        self.conn.commit()
        cursor.close()

    def delete_comment(self, task_id, username, content,timestamp):
        self.conn.execute("DELETE FROM comments WHERE task_id = ? AND username = ? AND content = ? And timestamp = ?",
                          (task_id, username, content,timestamp))
        self.conn.commit()

    def get_comment(self, task_id, username, content,timestamp):
        cursor = self.conn.execute("SELECT username, content, timestamp FROM comments WHERE task_id = ? AND username = ? AND content = ? And timestamp = ?",
                                   (task_id, username, content,timestamp,))
        row = cursor.fetchone()
        if row:
           return Comment(username=row[0], content=row[1], timestamp=row[2]) 
        return None


