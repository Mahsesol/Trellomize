import flet as ft
from flet import *
import sqlite3
import hashlib
import re
from project import Project
from user import User
from database import Database
import uuid
from task import *
from datetime import datetime, timedelta


DB_FILE = 'database.db'


   

class LoginPage(UserControl):
    def __init__(self, db, on_login=None):
        super().__init__()
        self.db = db
        self.on_login = on_login

    def build(self):
        self.username = TextField(label="Username")
        self.password = TextField(label="Password", password=True, can_reveal_password=True)
        self.error_message = Text(value="", color=colors.RED)
        return Column([
            self.username,
            self.password,
            ElevatedButton("Login", on_click=self.login),
            self.error_message
        ])

    def login(self, e):
        username = self.username.value
        password = self.password.value

        if self.check_credentials(username, password):
            if self.check_active(username):
                if self.on_login:
                    self.on_login(username)
                else:
                    self.page.snack_bar = ft.SnackBar(
                        content=Text("Login successful!"),
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    self.page.go("/main")
            else:
                self.error_message.value = "Your account is inactive. Please contact the administrator."
        else:
            self.error_message.value = "Invalid username or password!"
        self.update()

    def check_credentials(self, username, password):
        hashed_password = self.db._hash_password(password)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        result = self.db.conn.execute(query, (username, hashed_password)).fetchone()
        return result is not None

    def check_active(self, username):
        query = "SELECT active FROM users WHERE username=?"
        result = self.db.conn.execute(query, (username,)).fetchone()
        return result[0] if result else False

    def show_signup(self, e):
        self.page.go("/signup")

class SignupPage(UserControl):
    def __init__(self, db, on_signup=None):
        super().__init__()
        self.db = db
        self.on_signup = on_signup

    def build(self):
        self.username = TextField(label="Username")
        self.email = TextField(label="Email")
        self.password = TextField(label="Password", password=True, can_reveal_password=True)
        self.error_message = Text(value="", color=colors.RED)
        return Column([
            self.username,
            self.email,
            self.password,
            ElevatedButton("Sign Up", on_click=self.signup),
            self.error_message
        ])

    def signup(self, e):
        username = self.username.value
        email = self.email.value
        password = self.password.value

        if self.username_exists(username):
            self.error_message.value = "Username already taken!"
        elif len(password) < 6:
            self.error_message.value = "Password must be at least 6 characters long!"
        elif not username or not email or not self.check_email(email) or not password:
            self.error_message.value = "Invalid input!"
        else:
            self.db.add_user(username, password, email)
            if self.on_signup:
                self.on_signup(username)
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=Text("Account created successfully!"),
                )
                self.page.snack_bar.open = True
                self.page.update()
                self.page.go("/login")
        self.update()

    def username_exists(self, username):
        query = "SELECT * FROM users WHERE username=?"
        result = self.db.conn.execute(query, (username,)).fetchone()
        return result is not None

    def check_email(self, email):
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


class MainPage(UserControl):
    def __init__(self, db, username, page):
        super().__init__()
        self.db = db
        self.username = username
        self.page = page

    def build(self):
        buttons = [
            ElevatedButton("Create Project", on_click=self.create_project),
            ElevatedButton("Show Projects", on_click=self.show_projects)
        ]

        if self.db.is_admin(self.username):
            buttons.append(ElevatedButton("Manage Users", on_click=self.manage_users))

        return Column([
            Text(f"Welcome, {self.username}!"),
            *buttons
        ])

    def create_project(self, e):
        create_project_page = CreateProjectPage(self.db, self.username, self.page)
        self.page.views.append(
            ft.View(
                "/create_project",
                [create_project_page],
            )
        )
        self.page.update()

    def show_projects(self, e):
        projects_list = ProjectListPage(self.db , self.page)
        self.page.go(f"/projects_list")
        self.page.update()

    def manage_users(self, e):
        self.page.go("/manage_users")

    def project_management(self, project_id):
        project_management_page = ProjectManagementPage(self.db, self.username, project_id, self.page)
        self.page.views.append(
            ft.View(
                "/project_management",
                [project_management_page],
            )
        )
        self.page.update()

class ProjectListPage(UserControl):
    def __init__(self, db, page):
        super().__init__()
        self.db = db
        self.page = page
        self.username = self.db.get_current_user(self.page).get_username()
        self.user_id = self.db.get_current_user_id(self.page)

    def build(self):
      
        leader_projects = self.db.get_user_project_leader(self.user_id)
        member_projects = self.db.get_user_project_member(self.user_id)
        print(leader_projects)
        print(member_projects)
        leader_controls = []
        for project in leader_projects:
            leader_controls.append(Row([
                Text(project.get_project_name()),
                ElevatedButton("Manage", on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id))
            ]))

        # Create a list of controls for member projects
        member_controls = []
        for project in member_projects:
            member_controls.append(Row([
                Text(project.get_project_name()),
                ElevatedButton("Manage", on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id))
            ]))

        return Column([
            Text("Project List", size=20),
            Text(f"Projects you are the leader of, {self.username}:", size=15),
            *leader_controls,
            Text(f"Projects you are a member of, {self.username}:", size=15),
            *member_controls,
            ElevatedButton("Back", on_click=lambda e: self.page.go("/main"))
        ])

    def manage_project(self, project_id):
        project_management_page = ProjectManagementPage(self.db, self.username, project_id, self.page)
        self.page.views.append(
            ft.View(
                "/project_management",
                [project_management_page],
            )
        )
        self.page.update()



class ManageUsersPage(UserControl):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def build(self):
        return Column([
            Text("User Management", size=20),
            ElevatedButton("Active Users", on_click=self.show_active_users),
            ElevatedButton("Inactive Users", on_click=self.show_inactive_users),
            ElevatedButton("Back", on_click=lambda e: self.page.go("/main"))  # Add a back button to return to the main page
        ])

    def show_active_users(self, e):
        self.page.go("/active_users")

    def show_inactive_users(self, e):
        self.page.go("/inactive_users")

    def get_active_users_list(self):
        users = self.db.get_all_active_users()
        if not users:
            return Column([Text("No active users found")])
        else:
            return Column([
                Row([
                    Text(user.username),  # Display username
                    ElevatedButton("Inactivate", on_click=lambda e, user=user: self.inactivate_user(user.user_id))
                ]) for user in users
            ])



class ActiveUsersPage(UserControl):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def build(self):
        self.user_list = self.get_active_users_list()
        return Column([
            Text("Active Users", size=20),
            self.user_list,
            ElevatedButton("Back", on_click=lambda e: self.page.go("/manage_users"))  # Back button to go back to manage users
        ])

    def get_active_users_list(self):
        users = self.db.get_all_active_users()
        if not users:
            return Column([Text("No active users found")])
        else:
            return Column([
                Row([
                    Text(user.username),  # Display username
                    ElevatedButton("Inactivate", on_click=lambda e, user=user: self.inactivate_user(user.user_id))
                ]) for user in users
            ])

    def inactivate_user(self, user_id):
        self.db.inactivate_user(user_id)
        self.update_active_users_list()

    def update_active_users_list(self):
        self.user_list.controls.clear()
        self.user_list.controls.extend(self.get_active_users_list().controls)
        self.update()

class InactiveUsersPage(UserControl):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def build(self):
        self.user_list = self.get_inactive_users_list()
        return Column([
            Text("Inactive Users", size=20),
            self.user_list,
            ElevatedButton("Back", on_click=lambda e: self.page.go("/manage_users"))  # Back button to go back to manage users
        ])

    def get_inactive_users_list(self):
        users = self.db.get_all_inactive_users()
        if not users:
            return Column([Text("No inactive users found")])
        else:
            return Column([
                Row([
                    Text(user.username),  # Display username
                    ElevatedButton("Activate", on_click=lambda e, user=user: self.activate_user(user.user_id))
                ]) for user in users
            ])

    def activate_user(self, user_id):
        self.db.activate_user(user_id)
        self.update_inactive_users_list()

    def update_inactive_users_list(self):
        self.user_list.controls.clear()
        self.user_list.controls.extend(self.get_inactive_users_list().controls)
        self.update()

class CreateProjectPage(UserControl):
    def __init__(self, db, username, page):
        super().__init__()
        self.db = db
        self.username = username
        self.page = page
        self.new_project_name = ""
        self.new_project_id = ""
        self.member_checkboxes = []

    def build(self):
        self.project_name_field = TextField(label="Project Name", width=300)
        self.project_id_field = TextField(label="Project ID (Recommended: Leave blank for auto-generated)", width=300)

        self.select_members_column = Column()

        return Column(
            [
                Text("Create a New Project", size=30),
                self.project_name_field,
                self.project_id_field,
                ElevatedButton("Next", on_click=self.select_members),
                ElevatedButton("Cancel", on_click=self.cancel_dialog),
                self.select_members_column
            ]
        )

    def select_members(self, e):
        project_name = self.project_name_field.value
        project_id = self.project_id_field.value

        if not project_name:
            self.show_snackbar("Please enter a project name!")
            return

        if not project_id:
            project_id = str(uuid.uuid4())

        self.set_new_project_name(project_name)
        self.set_new_project_id(project_id)

        active_users = self.db.get_all_active_users()
        self.member_checkboxes.clear()

        # Exclude the current user from the list of active users
        current_user_id = self.db.get_user_by_username(self.username).get_id()
        active_users = [user for user in active_users if user.get_id() != current_user_id]

        for user in active_users:
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        self.select_members_column.controls = [
            Text(f"Select members for project '{project_name}':", size=30),
            Column(self.member_checkboxes),
            ElevatedButton("Done", on_click=self.create_project_confirm),
            ElevatedButton("Cancel", on_click=self.cancel_dialog)
        ]
        self.update()

    def create_project_confirm(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        if not selected_user_ids:
            self.show_snackbar("Please select at least one member!")
            return

        # Get the current user's ID as the leader ID
        leader_id = self.db.get_user_by_username(self.username).get_id()
        self.db.add_project(self.get_new_project_id(), self.get_new_project_name(), leader_id, selected_user_ids)

        self.show_snackbar(f"Project '{self.get_new_project_name()}' created successfully!")

        # Navigate to the project management page
        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.go("/main")

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar = snackbar
        self.page.snack_bar.open = True
        self.page.update()

    def get_new_project_name(self):
        return self.new_project_name

    def set_new_project_name(self, new_project_name):
        self.new_project_name = new_project_name

    def get_new_project_id(self):
        return self.new_project_id

    def set_new_project_id(self, new_project_id):
        self.new_project_id = new_project_id

class ProjectManagementPage(UserControl):
    def __init__(self, db, username, project_id, page):
        super().__init__()
        self.db = db
        self.username = username
        self.project_id = project_id
        self.page = page

    def build(self):
        project = self.db.get_project(self.project_id)
        

        # Check if project exists
        if project:
            # Check if the current user is the leader of the project
            is_leader = self.db.get_user_by_username(self.username).get_id() == project.get_leader_id()
            if is_leader:
                buttons = [
                    ElevatedButton("See Project Members", on_click=self.show_members),
                    ElevatedButton("See Tasks", on_click=self.show_tasks),
                    ElevatedButton("Add Task", on_click=self.add_task),
                    ElevatedButton("Back", on_click=lambda e: self.page.go("/main"))
                ]
            else:
                buttons = [
                    ElevatedButton("See Project Members", on_click=self.show_members),
                    ElevatedButton("See Tasks", on_click=self.show_tasks),
                    ElevatedButton("Back", on_click=lambda e: self.page.go("/main"))
                ]

            return Column([
                Text(f"Project: {project.get_project_name()}", size=30),
                *buttons
            ])
        else:
            return Text("Project not found", size=30)


    def show_members(self, e):
         project_members = ProjectMembersWindow(self.db, self.project_id, self.page)
         self.page.go(f"/project_members/{self.project_id}")
         self.page.update()
  

    def select_assignees_done(self, e):
        self.selected_assignees = [cb.key for cb in self.member_checkboxes if cb.value]
        self.page.go("/project_management")

    def remove_member(self, member_id):
        self.db.remove_project_member(self.project_id, member_id)
        self.show_snackbar("Member removed successfully")
        self.show_members(None)

    def add_task(self, e):
        #print("Add Task button clicked")
        add_task = AddTaskWindow(self.db, self.project_id, self.page)
        # self.page.dialog = add_task
        # self.page.dialog.open = True
        self.page.go(f"/add_task/{self.project_id}")
        self.page.update()


    def show_tasks(self, e):
        show_tasks = ShowTasksWindow(self.db, self.project_id, self.page)
        self.page.go(f"/show_tasks/{self.project_id}")
        self.page.update()
        # show_tasks = ShowTasksWindow(self.db, self.project_id, self.page)
        # self.page.update()
        # self.page.show_dialog(show_tasks)
        
   

    def get_db(self):
        return self.db

    def set_db(self, db):
        self.db = db

    def get_username(self):
        return self.username

    def set_username(self, username):
        self.username = username

    def get_project_id(self):
        return self.project_id

    def set_project_id(self, project_id):
        self.project_id = project_id

    def get_page(self):
        return self.page

    def set_page(self, page):
        self.page = page


class ShowTasksWindow(UserControl):
    def __init__(self, db, project_id, page):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self.page = page

    def build(self):
        project = self.db.get_project(self.project_id)
        tasks = self.db.get_project_tasks(self.project_id)
        tasks_by_status = self.group_tasks_by_status(tasks)
        
        task_controls = []
        if not tasks:
            task_controls.append(ft.Text("No tasks in this project yet.", size=20))
        else:
            for status, task_list in tasks_by_status.items():
                task_data_rows = []
                for task in sorted(task_list, key=lambda task: task.get_priority(), reverse=False):
                    

                    assignees =", ".join([ assignee_id.get_username() for assignee_id in task.get_assignees()])
                    task_data_rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(task.get_title())),
                        ft.DataCell(ft.Text(str(task.get_start_datetime()))),
                        ft.DataCell(ft.Text(str(task.get_end_datetime()))),
                        ft.DataCell(ft.Text(task.get_priority().name)),
                        ft.DataCell(ft.Text(assignees)),
                        ft.DataCell(ft.ElevatedButton("Show Details", on_click=lambda e, task_id=task.get_task_id(): self.show_task_details(task_id)))
                    ]))

                task_data_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Title")),
                        ft.DataColumn(ft.Text("Start Date")),
                        ft.DataColumn(ft.Text("End Date")),
                        ft.DataColumn(ft.Text("Priority")),
                        ft.DataColumn(ft.Text("Assignees")),
                        ft.DataColumn(ft.Text("Actions")),
                    ],
                    rows=task_data_rows
                )

                task_controls.append(ft.Column([
                    ft.Text(f"{status.name} Tasks", size=20),
                    task_data_table
                ]))

        return ft.Column([
            ft.Text(f"Tasks of Project '{project.get_project_name()}'", size=30),
            *task_controls,
            ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/project_management/{self.project_id}"))
        ])



    def group_tasks_by_status(self, tasks):
        tasks_by_status = {}
        for task in tasks:
            status = task.get_status()
            if status not in tasks_by_status:
                tasks_by_status[status] = []
            tasks_by_status[status].append(task)
        return tasks_by_status

    def show_task_details(self, task_id):
        show_task_details = ShowTaskDetailsWindow(self.db, task_id , self.page)
       # self.page.show_dialog(show_task_details)
        self.page.go(f"/show_task_details/{task_id}")
        self.page.update()

    def close_window(self):
        self.page.close_dialog()

class ShowTaskDetailsWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):

        task_id = self.task_id
        task = self.db.get_task(self.task_id)
        project_id = task.get_project_id()
        project = self.db.get_project(project_id)

        task_details_controls = [
           # Text(f"Task: {task.title}", size=30),
            Text(f"Description: {task.description}"),
            Text(f"Priority: {task.priority.name}"),
            Text(f"Status: {task.status.name}"),
            Text(f"Start Date: {task.start_datetime}"),
            Text(f"End Date: {task.end_datetime}"),
            Text(f"Assignees: {', '.join([assignee_id.get_username() for assignee_id in task.get_assignees()])}"),
            ElevatedButton("Show Comments", on_click=lambda e: self.show_comments(task_id)),
            ElevatedButton("Show History", on_click=lambda e: self.show_history(task_id)),
           # ElevatedButton("Back", on_click=lambda e: self.close_window())
        ]
       
        assinee_names =[]
        for task_assignee in task.get_assignees():
              assinee_names.append(task_assignee.get_username())
        if self.db.get_current_user(self.page).get_username() in assinee_names:
            task_details_controls.append(ElevatedButton("Change Status", on_click=lambda e: self.change_task_status(task_id)))

        if self.db.get_current_user_id(self.page) == project.get_leader_id():
            task_details_controls.append(ElevatedButton("Add Assignees", on_click=lambda e: self.add_assignees(task_id)))
            task_details_controls.append(ElevatedButton("Remove Assignees", on_click=lambda e: self.remove_assignees(task_id)))
        
        task_details_controls.append(ElevatedButton("Back", on_click=lambda e: self.close_window()))

        return ft.Column([           
            ft.Text(f"Task: {task.get_title()} for Project: {project.get_project_name()}", size=30),  # Show project name
            *task_details_controls])



    def close_window(self):
        self.page.close_dialog()

# class ShowAssigneesWindow(UserControl):
#     def __init__(self, db, task_id, page):
#         super().__init__()
#         self.db = db
#         self.task_id = task_id
#         self.page = page

#     def build(self):
#         task = self.db.get_task(self.task_id)
#         assignees = task.get_assignees()

#         assignee_controls = []
#         for assignee_id in assignees:
#             user = self.db.get_user_by_id(assignee_id)
#             assignee_controls.append(Text(user.get_username()))

#         self.page.views[-1].controls = [
#             Text(f"Assignees for Task: {task.title}", size=30),
#             Column(assignee_controls),
#             ElevatedButton("Back", on_click=lambda e: self.close_window())
#         ]
#         self.page.update()

#     def close_window(self):
#         self.page.close_dialog()

class ShowCommentsWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        task = self.db.get_task(self.task_id)

        comment_controls = []
        for comment in task.get_comments():
            comment_controls.append(Text(f"{comment.get_username()}: {comment.get_content()}"))

        self.page.views[-1].controls = [
            Text(f"Comments for Task: {task.title}", size=30),
            Column(comment_controls),
            ElevatedButton("Back", on_click=lambda e: self.close_window())
        ]
        self.page.update()

    def close_window(self):
        self.page.close_dialog()

class ShowHistoryWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        task = self.db.get_task(self.task_id)
        history = self.db.get_task_history(self.task_id)

        history_controls = []
        for record in history:
            history_controls.append(Text(f"{record.get_timestamp()}: {record.get_action()} by {record.get_author()}"))

        self.page.views[-1].controls = [
            Text(f"History for Task: {task.title}", size=30),
            Column(history_controls),
            ElevatedButton("Back", on_click=lambda e: self.close_window())
        ]
        self.page.update()

    def close_window(self):
        self.page.close_dialog()

class AddAssigneesWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        active_users = self.db.get_all_active_users()

        # Exclude current assignees and the current user
        current_assignees = self.db.get_task(self.task_id).get_assignees()
        current_user_id = self.db.get_current_user_id(self.page)
        active_users = [user for user in active_users if user.get_id() not in current_assignees and user.get_id() != current_user_id]

        self.member_checkboxes = []
        for user in active_users:
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        return Column([
            Text("Add Assignees to Task", size=30),
            Column(self.member_checkboxes),
            ElevatedButton("Save", on_click=self.save_assignees),
            ElevatedButton("Cancel", on_click=self.cancel_dialog)
        ])

    def save_assignees(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        task = self.db.get_task(self.task_id)
        for user_id in selected_user_ids:
            task.assign_user(user_id)
            self.db.add_task_history(self.task_id, f"Assigned user {user_id}", self.db.get_current_user_id(self.page))

        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Assignees added successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/project_management/{self.task_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.dialog = None
        self.page.update()

class RemoveAssigneesWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        task = self.db.get_task(self.task_id)
        current_assignees = task.get_assignees()

        self.member_checkboxes = []
        for assignee_id in current_assignees:
            user = self.db.get_user_by_id(assignee_id)
            cb = Checkbox(label=user.get_username(), key=user.get_id(), value=True)
            self.member_checkboxes.append(cb)

        return Column([
            Text("Remove Assignees from Task", size=30),
            Column(self.member_checkboxes),
            ElevatedButton("Save", on_click=self.remove_assignees),
            ElevatedButton("Cancel", on_click=self.cancel_dialog)
        ])

    def remove_assignees(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        task = self.db.get_task(self.task_id)
        for user_id in selected_user_ids:
            task.unassign_user(user_id)
            self.db.add_task_history(self.task_id, f"Unassigned user {user_id}", self.db.get_current_user_id(self.page))

        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Assignees removed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/project_management/{self.task_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.dialog = None
        self.page.update()




    



class ProjectMembersWindow(UserControl):
    def __init__(self, db, project_id, page):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self.page = page
        self.member_checkboxes = []

    def build(self):
        project_members = self.db.get_project_members(self.project_id)
        self.member_checkboxes.clear()

        for member in project_members:
            cb = Checkbox(label=member.get_username(), key=member.get_id())
            self.member_checkboxes.append(cb)

        project = self.db.get_project(self.project_id)
        leader_id = project.get_leader_id()

        current_user_id = self.db.get_current_user_id(self.page)

        if current_user_id == leader_id:
            return Column([
                Text("Project Members", size=30),
                Column(self.member_checkboxes),
                ElevatedButton("Remove Selected Members", on_click=self.remove_members),
                ElevatedButton("Back", on_click=self.cancel_dialog)
            ])
        else:
            return Column([
                Text("Project Members", size=30),
                Column(self.member_checkboxes),
                ElevatedButton("Back", on_click=self.cancel_dialog)
            ])

    def remove_members(self, e):
        selected_member_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        for member_id in selected_member_ids:
            self.db.remove_project_member(self.project_id, member_id)

        self.update_member_checkboxes()
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Members removed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()

    def update_member_checkboxes(self):
        project_members = self.db.get_project_members(self.project_id)
        self.member_checkboxes.clear()

        for member in project_members:
            cb = Checkbox(label=member.get_username(), key=member.get_id(), value=True)
            self.member_checkboxes.append(cb)

        self.update()

    def cancel_dialog(self, e):
        self.page.close_dialog()

class AddTaskWindow(UserControl):
    def __init__(self, db, project_id, page):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self.page = page
        self.start_date_error = None
        self.end_date_error = None

    def build(self):
        self.title_field = TextField(label="Title")
        self.description_field = TextField(label="Description")
        self.priority_dropdown = Dropdown(
            label="Priority",
            options=[
                ft.dropdown.Option("CRITICAL"),
                ft.dropdown.Option("HIGH"),
                ft.dropdown.Option("MEDIUM"),
                ft.dropdown.Option("LOW")
            ],
            value="LOW"  # Default value for priority
        )
        self.start_date_field = TextField(label="Start Date (YYYY-MM-DD HH:MM:SS)")
        self.end_date_field = TextField(label="End Date (YYYY-MM-DD HH:MM:SS)")
        self.member_checkboxes = []
        self.choose_assignees_label = Text("Choose Assignees:")

        active_users = self.db.get_project_members(self.project_id)
        active_users.append(self.db.get_user_by_id(self.db.get_project(self.project_id).get_leader_id()))
        for user in active_users:
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        return Column([
            Text("Add a New Task", size=30),
            self.title_field,
            self.description_field,
            self.priority_dropdown,
            self.start_date_field,
            self.end_date_field,
            self.choose_assignees_label,
            Column(self.member_checkboxes),
            ElevatedButton("Save", on_click=self.save_task),
            ElevatedButton("Cancel", on_click=self.cancel_dialog)
        ])

    def validate_fields(self):
        title = self.title_field.value
        description = self.description_field.value
        start_date = self.start_date_field.value
        end_date = self.end_date_field.value

        if not title:
            self.show_snackbar("Title field cannot be empty.")
            return False
        if not description:
            self.show_snackbar("Description field cannot be empty.")
            return False
        if not start_date:
            self.start_date_error = "Start date cannot be empty."
        elif not self.is_valid_date(start_date):
            self.start_date_error = "Invalid start date format. Please use YYYY-MM-DD HH:MM:SS."
        if not end_date:
            self.end_date_error = "End date cannot be empty."
        elif not self.is_valid_date(end_date):
            self.end_date_error = "Invalid end date format. Please use YYYY-MM-DD HH:MM:SS."

        return True

    def save_task(self, e):
        if not self.validate_fields():
            return

        start_date = self.start_date_field.value
        end_date = self.end_date_field.value

        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not end_date:
            end_date = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        selected_assignees = [cb.key for cb in self.member_checkboxes if cb.value]

        # Create a new Task object
        new_task = Task(
            project_id=self.project_id,
            title=self.title_field.value,
            description=self.description_field.value,
            priority=self.priority_dropdown.value,
            status="BACKLOG",
            assignees=selected_assignees,
            start_datetime=self.parse_date(start_date),
            end_datetime=self.parse_date(end_date)
           
        )

        # Add the task to the database
        self.db.add_task(new_task)

        # Close the dialog and show a success message
        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Task added successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/project_management/{self.project_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.dialog = None
        self.page.update()

    def is_valid_date(self, date_string):
        try:
            datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return True
        except ValueError:
            return False

    def parse_date(self, date_string):
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar = snackbar
        self.page.snack_bar.open = True
        self.page.update()

    



def main(page: ft.Page):
    db = Database()

    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.Text("Do you want to login or sign up?", size=30),
                        ft.ElevatedButton("Login", on_click=lambda e: page.go("/login")),
                        ft.ElevatedButton("Sign Up", on_click=lambda e: page.go("/signup")),
                    ],
                )
            )
        elif page.route == "/login":
            page.views.append(
                ft.View(
                    "/login",
                    [LoginPage(db, on_login=lambda username: on_login(page, username))],
                )
            )
        elif page.route == "/signup":
            page.views.append(
                ft.View(
                    "/signup",
                    [SignupPage(db, on_signup=lambda username: on_signup(page, username))],
                )
            )
        elif page.route == "/main":
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    "/main",
                    [MainPage(db, username, page)],
                )
            )
        elif page.route == "/projects_list":
            page.views.append(
                ft.View(
                    "/projects_list",
                    [ProjectListPage(db,page)],
                )
            )   
        elif page.route == "/manage_users":
            page.views.append(
                ft.View(
                    "/manage_users",
                    [ManageUsersPage(db)],
                )
            )
        elif page.route == "/active_users":
            page.views.append(
                ft.View(
                    "/active_users",
                    [ActiveUsersPage(db)],
                )
            )
        elif page.route == "/inactive_users":
            page.views.append(
                ft.View(
                    "/inactive_users",
                    [InactiveUsersPage(db)],
                )
            )
        elif page.route == "/create_project":
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    "/create_project",
                    [CreateProjectPage(db, username, page)],
                )
            )
        elif page.route.startswith("/project_management"):
            project_id = page.route.split("/")[-1]
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    f"/project_management/{project_id}",
                    [ProjectManagementPage(db, username, project_id, page)],
                )
            )
        elif page.route.startswith("/add_task"):
            project_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/add_task/{project_id}",
                    [AddTaskWindow(db, project_id, page)],
                )
            )
        elif page.route.startswith("/project_members"):
            project_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/project_members/{project_id}",
                    [ProjectMembersWindow(db, project_id, page)],
                )
            )
        elif page.route.startswith("/show_tasks"):
             project_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/show_tasks/{project_id}",
                    [ShowTasksWindow(db, project_id, page)],
                )
            )
        elif page.route.startswith("/show_task_details"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/show_task_details/{task_id}",
                    [ShowTaskDetailsWindow(db, task_id, page)],
                )
            ) 
            
        page.update()

    def on_login(page, username):
        page.session.set("username", username)
        page.go("/main")

    def on_signup(page, username):
        page.session.set("username", username)
        page.go("/main")

    page.on_route_change = route_change
    page.go(page.route)

ft.app(target=main, view=ft.AppView.FLET_APP)



# class TaskDetailsPage(UserControl):
#     def __init__(self, db, task_id, page):
#         super().__init__()
#         self.db = db
#         self.task_id = task_id
#         self.page = page

#     def build(self):
#         task = self.db.get_task(self.task_id)
#         comments = self.db.get_task_comments(self.task_id)
#         history = self.db.get_task_history(self.task_id)
        
#         comment_controls = []
#         for comment in comments:
#             comment_controls.append(ft.Text(f"{comment.username} ({comment.timestamp}): {comment.content}"))

#         history_controls = []
#         for record in history:
#             history_controls.append(ft.Text(f"{record['timestamp']}: {record['action']} by {record['author']}"))

#         self.priority_dropdown = ft.Dropdown(
#             label="Priority",
#             options=[
#                 ft.DropdownOption("CRITICAL"),
#                 ft.DropdownOption("HIGH"),
#                 ft.DropdownOption("MEDIUM"),
#                 ft.DropdownOption("LOW")
#             ],
#             value=task.priority.name
#         )

#         self.end_date_picker = ft.DatePicker(
#             label="End Date",
#             value=task.end_datetime.strftime("%Y-%m-%d")
#         )

#         self.comment_field = ft.TextField(
#             label="Add Comment"
#         )

#         return ft.Column([
#             ft.Text(f"Task: {task.title}", size=30),
#             ft.Text(f"Description: {task.description}"),
#             ft.Text(f"Priority: {task.priority.name}"),
#             ft.Text(f"Status: {task.status.name}"),
#             ft.Text(f"Start Date: {task.start_datetime}"),f
#             ft.Text(f"End Date: {task.end_datetime}"),
#             ft.Text("Comments:"),
#             ft.Column(comment_controls),
#             ft.Text("History:"),
#             ft.Column(history_controls),
#             self.priority_dropdown,
#             ft.ElevatedButton("Change Priority", on_click=self.change_task_priority),
#             self.end_date_picker,
#             ft.ElevatedButton("Change End Date", on_click=self.change_task_end_date),
#             self.comment_field,
#             ft.ElevatedButton("Add Comment", on_click=self.add_task_comment),
#             ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/project_management/{task.project_id}"))
#         ])

#     def change_task_priority(self, e):
#         new_priority = self.priority_dropdown.value
#         self.db.update_task_priority(self.task_id, new_priority)
#         self.db.add_task_history(self.task_id, f"Priority changed to {new_priority}", self.page.session.get("username"))
#         self.page.go(f"/task_details/{self.task_id}")

#     def change_task_end_date(self, e):
#         new_end_date = self.end_date_picker.value
#         self.db.update_task_end_date(self.task_id, new_end_date)
#         self.db.add_task_history(self.task_id, f"End date changed to {new_end_date}", self.page.session.get("username"))
#         self.page.go(f"/task_details/{self.task_id}")

#     def add_task_comment(self, e):
#         comment_content = self.comment_field.value
#         if comment_content:
#             username = self.page.session.get("username")
#             self.db.add_task_comment(self.task_id, username, comment_content)
#             self.db.add_task_history(self.task_id, f"Comment added by {username}", username)
#             self.page.go(f"/task_details/{self.task_id}")
#         else:
#             self.page.show_snackbar("Comment cannot be empty.")
