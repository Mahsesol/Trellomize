import unittest
from database import Database
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
import os 

class TestDatabase(unittest.TestCase):
    DB_FILE = 'test_database.db' 

    def setUp(self):
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)  
        self.db = Database(self.DB_FILE) 
        self.db.create_tables()  


    def tearDown(self):
        self.db.conn.close()
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)

    def test_add_user(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user[1], "test_user") 

    def test_get_user(self):
        self.db.add_user("test_user2", "password", "test_user2@example.com")
        user = self.db.get_user("test_user2", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user[1], "test_user2")

    def test_add_project(self):
        self.db.add_user("test_leader", "password", "leader@example.com")
        leader = self.db.get_user("test_leader", "password")
        self.db.add_project("test_project_id", "Test Project", leader[0], [])
        project = self.db.get_project("test_project_id")
        self.assertIsNotNone(project)
        self.assertEqual(project.get_project_name(), "Test Project")

    def test_add_task(self):
        self.db.add_project("project_id", "Project 1", 1, [])
        task = Task(task_id="1", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status='BACKLOG', assignees=[1, 2])
        self.db.add_task(task)
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task.get_task_id(),))
        task_row = cursor.fetchone()
        self.assertIsNotNone(task_row)
        self.assertEqual(task_row[2], "Task 1")
        
        cursor.execute("SELECT * FROM task_assignees WHERE task_id = ?", (task.get_task_id(),))
        assignees = cursor.fetchall()
        self.assertEqual(len(assignees), 2)
        self.assertIn((task.get_task_id(), 1), assignees)
        self.assertIn((task.get_task_id(), 2), assignees)

    def test_add_comment(self):
       self.db.add_user("user1", "password", "user1@example.com")
       self.db.add_project("project_id", "Project 1", 1, [])
       task = Task(task_id="1", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status='BACKLOG', assignees=[1])
       self.db.add_task(task)
       self.db.add_comment(1, "user1", "This is a comment.")
       cursor = self.db.conn.cursor()
       cursor.execute("SELECT * FROM comments WHERE task_id = ?", (1,))
       comments = cursor.fetchall()
       self.assertEqual(len(comments), 1)
       self.assertEqual(comments[0][2], "user1")  # Check the username
       self.assertEqual(comments[0][3], "This is a comment.")  # Check the comment content




    def test_get_task_history(self):
        self.db.add_project("project_id", "Project 1", 1, [])
        self.db.add_task_history(1, "Created", "user1")
        self.db.add_task_history(1, "Updated", "user2")

        history = self.db.get_task_history(1)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].action, "Created")
        self.assertEqual(history[1].action, "Updated")


    def test_hash_password(self):
        password = "password123"
        hashed_password = self.db._hash_password(password)
        expected_hash = hashlib.sha256(password.encode()).hexdigest()
        self.assertEqual(hashed_password, expected_hash)

    def test_add_admin(self):
        self.db.add_admin("admin_user", "admin_password")
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ("admin_user",))
        admin = cursor.fetchone()
        self.assertIsNotNone(admin)
        self.assertEqual(admin[3], "admin@example.com")  
        self.assertTrue(admin[5])  

    def test_create_admin(self):
        self.db.create_admin("admin_user2", "admin_password",self.DB_FILE)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", ("admin_user2",))
        admin = cursor.fetchone()
        self.assertIsNotNone(admin)
        self.assertEqual(admin[3], "admin@example.com")  
        self.assertTrue(admin[5]) 

    def test_is_admin(self):
        self.db.add_admin("admin_user3", "admin_password")
        is_admin = self.db.is_admin("admin_user3")
        self.assertTrue(is_admin)
        is_not_admin = self.db.is_admin("non_admin_user")
        self.assertFalse(is_not_admin)


    def test_admin_exists(self):
        self.assertFalse(self.db.admin_exists())
        self.db.add_admin("admin_user", "admin_password")
        self.assertTrue(self.db.admin_exists())

    def test_get_user(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        self.assertIsNotNone(user)
        self.assertEqual(user[1], "test_user")

    def test_get_user_by_username(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        self.db.add_project("project_id", "Project 1", 1, [])
        user = self.db.get_user_by_username("test_user")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test_user")
        self.assertEqual(user.email, "test_user@example.com")
        self.assertEqual(len(user.projects), 1)

    def test_get_all_users(self):
        self.db.add_user("test_user1", "password", "test_user1@example.com")
        self.db.add_user("test_user2", "password", "test_user2@example.com")
        users = self.db.get_all_users()
        self.assertEqual(len(users), 2)
        usernames = [user.username for user in users]
        self.assertIn("test_user1", usernames)
        self.assertIn("test_user2", usernames)


    def test_get_all_active_users(self):
        self.db.add_user("active_user", "password", "active_user@example.com", active=1)
        self.db.add_user("inactive_user", "password", "inactive_user@example.com", active=0)
        active_users = self.db.get_all_active_users()
        self.assertEqual(len(active_users), 1)
        self.assertEqual(active_users[0].username, "active_user")

    def test_get_all_inactive_users(self):
        self.db.add_user("active_user", "password", "active_user@example.com", active=1)
        self.db.add_user("inactive_user", "password", "inactive_user@example.com", active=0)
        inactive_users = self.db.get_all_inactive_users()
        self.assertEqual(len(inactive_users), 1)
        self.assertEqual(inactive_users[0].username, "inactive_user")

    def test_inactivate_user(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user_by_username("test_user")
        self.db.inactivate_user(user.get_id())
        inactive_user = self.db.get_user_by_id(user.get_id())
        self.assertFalse(inactive_user.get_is_active())

    def test_activate_user(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        self.db.inactivate_user(user[0])
        self.db.activate_user(user[0])
        active_user = self.db.get_user_by_id(user[0])
        self.assertTrue(active_user.get_is_active)

    def test_get_project(self):
        self.db.add_user("test_leader", "password", "leader@example.com")
        leader = self.db.get_user("test_leader", "password")
        self.db.add_project("project_id", "Project 1", leader[0], [])
        project = self.db.get_project("project_id")
        self.assertIsNotNone(project)
        self.assertEqual(project.get_project_name(), "Project 1")

    def test_get_project_member_ids(self):
        self.db.add_user("user1", "password", "user1@example.com")
        self.db.add_user("user2", "password", "user2@example.com")
        user1 = self.db.get_user("user1", "password")
        user2 = self.db.get_user("user2", "password")
        self.db.add_project("project_id", "Project 1", user1[0], [])
        self.db.add_project_member("project_id", user1[0])
        self.db.add_project_member("project_id", user2[0])
        member_ids = self.db.get_project_member_ids("project_id")
        self.assertIn(user1[0], member_ids)
        self.assertIn(user2[0], member_ids)

    def test_get_user_by_id(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        retrieved_user = self.db.get_user_by_id(user[0])
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "test_user")

    def test_get_project_members(self):
        self.db.add_user("user1", "password", "user1@example.com")
        self.db.add_user("user2", "password", "user2@example.com")
        user1 = self.db.get_user("user1", "password")
        user2 = self.db.get_user("user2", "password")
        self.db.add_project("project_id", "Project 1", user1[0], [])
        self.db.add_project_member("project_id", user1[0])
        self.db.add_project_member("project_id", user2[0])
        members = self.db.get_project_members("project_id")
        self.assertEqual(len(members), 2)
        member_usernames = [member.username for member in members]
        self.assertIn("user1", member_usernames)
        self.assertIn("user2", member_usernames)

    def test_get_current_user_id(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        page = MockPage(session={"username": "test_user"})
        user_id = self.db.get_current_user_id(page)
        self.assertEqual(user_id, 1)

    def test_get_current_user_username(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        page = MockPage(session={"username": "test_user"})
        username = self.db.get_current_user_username(page)
        self.assertEqual(username, "test_user")

    def test_get_current_user(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        page = MockPage(session={"username": "test_user"})
        user = self.db.get_current_user(page)
        self.assertIsInstance(user, User)
        self.assertEqual(user.get_username(), "test_user")

    def test_add_project_member(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        self.db.add_project_member("project_id", user[0])
        member_ids = self.db.get_project_member_ids("project_id")
        self.assertIn(user[0], member_ids)

    def test_remove_project_member(self):
        self.db.add_user("test_user", "password", "test_user@example.com")
        user = self.db.get_user("test_user", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        self.db.add_project_member("project_id", user[0])
        self.db.remove_project_member("project_id", user[0])
        member_ids = self.db.get_project_member_ids("project_id")
        self.assertNotIn(user[0], member_ids)

    def test_get_task_assignees(self):
        self.db.add_user("user1", "password", "user1@example.com")
        self.db.add_user("user2", "password", "user2@example.com")
        user1 = self.db.get_user("user1", "password")
        user2 = self.db.get_user("user2", "password")
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status="BACKLOG", assignees=[user1[0], user2[0]])
        self.db.add_task(task)
        assignees = self.db.get_task_assignees("task_id")
        self.assertEqual(len(assignees), 2)
        self.assertIn(user1[0], assignees)
        self.assertIn(user2[0], assignees)

    def test_get_project_tasks(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        project_tasks = self.db.get_project_tasks("project_id")
        self.assertEqual(len(project_tasks), 0)

    def test_get_task(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status="BACKLOG", assignees=[])
        self.db.add_task(task)
        task = self.db.get_task("task_id")
        self.assertIsNotNone(task)
        self.assertEqual(task.get_title(), "Task 1")

    def test_add_assignee(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user1 = self.db.get_user("user1", "password")
        self.db.add_user("user2", "password", "user2@example.com")
        user2 = self.db.get_user("user2", "password")
        self.db.add_project("project_id", "Project 1", user1[0], [])
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status="BACKLOG", assignees=[])
        self.db.add_task(task)
        self.db.add_assignee("task_id", user1[0])
        self.db.add_assignee("task_id", user2[0])
        assignees = self.db.get_task_assignees("task_id")
        self.assertIn(user1[0], assignees)
        self.assertIn(user2[0], assignees)

    def test_remove_assignee(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user1 = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user1[0], [])
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status="BACKLOG", assignees=[user1[0]])
        self.db.add_task(task)
        self.db.remove_assignee("task_id", user1[0])
        assignees = self.db.get_task_assignees("task_id")
        self.assertNotIn(user1[0], assignees)

    def test_get_user_project_member(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        self.db.add_project_member("project_id", user[0])
        projects = self.db.get_user_project_member(user[0])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].get_project_id(), "project_id")

    def test_get_user_project_leader(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        projects = self.db.get_user_project_leader(user[0])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].get_project_id(), "project_id")


    def test_change_status(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="HIGH", status="BACKLOG", assignees=[])
        self.db.add_task(task)
        self.db.change_status("task_id", "TODO")
        updated_task = self.db.get_task("task_id")
        self.assertEqual(updated_task.get_status(), Status.TODO)

    def test_change_priority(self):
        self.db.add_user("user1", "password", "user1@example.com")
        user = self.db.get_user("user1", "password")
        self.db.add_project("project_id", "Project 1", user[0], [])
        task = Task(task_id="task_id", project_id="project_id", title="Task 1", description="Description", start_datetime=datetime.now(), end_datetime=datetime.now(), priority="LOW", status="BACKLOG", assignees=[])
        self.db.add_task(task)
        self.db.change_priority("task_id", Priority.HIGH)
        updated_task = self.db.get_task("task_id")
        self

    def test_delete_comment(self):
        self.db.conn.execute("INSERT INTO comments (task_id, username, content, timestamp) VALUES (?, ?, ?, ?)",
                             ("task1", "user1", "comment1", "2024-05-31 12:00:00"))
        self.db.delete_comment("task1", "user1", "comment1")
        comment = self.db.get_comment("task1", "user1", "comment1")
        self.assertIsNone(comment)

    def test_get_comment(self):
        self.db.conn.execute("INSERT INTO comments (task_id, username, content, timestamp) VALUES (?, ?, ?, ?)",
                             ("task1", "user1", "comment1", "2024-05-31 12:00:00"))
        comment = self.db.get_comment("task1", "user1", "comment1")
        self.assertIsNotNone(comment)
        self.assertEqual(comment.username, "user1")
        self.assertEqual(comment.content, "comment1")
        self.assertEqual(comment.timestamp, "2024-05-31 12:00:00")




class MockPage:
    def __init__(self, session=None):
        self.session = session or {}



if __name__ == '__main__':
    unittest.main()


