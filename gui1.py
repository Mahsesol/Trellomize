import flet as ft
from flet import *
import sqlite3
import hashlib
import re
from project import Project
from user import User
from history import History
from database import Database
import uuid
from task import *
from datetime import datetime, timedelta
import logging
import sys


DB_FILE = 'database.db'


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
   

def create_button(text, on_click):
    return ft.ElevatedButton(
        text,
        on_click=on_click,
        width= 1000,
        height= 50,
    )

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
            create_button("Login", on_click=self.login),
            Text("Don't have an account?!", size=14),
            create_button("Sign Up", on_click=self.show_signup),
            self.error_message
        ])

    def login(self, e):
        username = self.username.value
        password = self.password.value

        if self.check_credentials(username, password):
            if self.check_active(username):
                logger.info(f"User '{username}' logged in successfully")
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
                logger.warning(f"Inactive account login attempt for user: {username}")

        else:
            self.error_message.value = "Invalid username or password!"
            logger.warning(f"Invalid login attempt for user: {username}")
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
            create_button("Sign Up", on_click=self.signup),
            Text("Already have an account?!", size=14),
            create_button("Login", on_click=self.show_login),
            self.error_message
        ])

    def signup(self, e):
        username = self.username.value
        email = self.email.value
        password = self.password.value

        if self.username_exists(username):
            self.error_message.value = "Username already taken!"
            logger.warning(f"Signup attempt failed: Username '{username}' already taken")
        elif len(password) < 6:
            self.error_message.value = "Password must be at least 6 characters long!"
            logger.warning(f"Signup attempt failed for user '{username}': Password too short")
        elif not username or not email or not password:
            self.error_message.value = "Invalid input!"
            logger.warning(f"Signup attempt failed for user '{username}': Invalid input")
        elif not self.check_email(email) or not password:
            self.error_message.value = "Invalid email address!"
            logger.warning(f"Signup attempt failed for user '{username}': Invalid email")
        else:
            self.db.add_user(username, password, email)
            logger.info(f"User '{username}' created successfully")
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

    def show_login(self, e):
        self.page.go("/login")

class MainPage(UserControl):
    def __init__(self, db, username, page):
        super().__init__()
        self.db = db
        self.username = username
        self.page = page

    def build(self):
        buttons = [
            create_button("Create Project", on_click=self.create_project),
            create_button("Show Projects", on_click=self.show_projects),
            create_button("Log out of this account", on_click=lambda e: self.page.go("/"))
        ]

        if self.db.is_admin(self.username):
            buttons.append(create_button("Manage Users", on_click=self.manage_users))

        return Column([
            Text(f"Welcome, {self.username}!", size=20),
            *buttons
        ])

    def create_project(self, e):
        create_project_page = CreateProjectPage(self.db, self.username, self.page)
        self.page.views.append(
            ft.View(
                "/create_project",
                [create_project_page],
                scroll= ScrollMode.AUTO,
                bgcolor=self.page.theme.color_scheme.background,
                # alignment=MainAxisAlignment.START,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        self.page.update()

    def show_projects(self, e):
        logger.info(f"User {self.username} requested to see their projects")
        projects_list = ProjectListPage(self.db, self.page)
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
                # Text(project.get_project_name()),
                create_button(f"Manage {project.get_project_name()}", on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id))
            ], width=1000))
        if not leader_projects:
            leader_controls.append(Text("No projects found.", italic=True))

        member_controls = []
        for project in member_projects:
            member_controls.append(Row([
                # Text(project.get_project_name()),
                create_button(f"Manage {project.get_project_name()}", on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id))
            ], width=1000))
        if not member_projects:
            member_controls.append(Text("No projects found.", italic=True))

        return Column([
            Text("Project List", size=20),
            Text(f"Projects you are the leader of, {self.username}:", size=15),
            *leader_controls,
            Text(f"Projects you are a member of, {self.username}:", size=15),
            *member_controls,
            create_button("Back", on_click=lambda e: self.page.go("/main"))
        ], width=1000)

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
            create_button("Active Users", on_click=self.show_active_users),
            create_button("Inactive Users", on_click=self.show_inactive_users),
            create_button("Back", on_click=lambda e: self.page.go("/main"))
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
                    Text(user.username),
                    create_button("Inactivate", on_click=lambda e, user=user: self.inactivate_user(user.user_id))
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
                    Text(user.username),  
                    ElevatedButton("Inactivate", on_click=lambda e, user=user: self.inactivate_user(user.user_id))
                ]) for user in users
            ])

    def inactivate_user(self, user_id):
        self.db.inactivate_user(user_id)
        self.update_active_users_list()
        username = self.db.get_user(user_id).get_username()
        logger.info(f"User '{username}' has been inactivated by admin")

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
            ElevatedButton("Back", on_click=lambda e: self.page.go("/manage_users"))  
        ])

    def get_inactive_users_list(self):
        users = self.db.get_all_inactive_users()
        if not users:
            return Column([Text("No inactive users found")])
        else:
            return Column([
                Row([
                    Text(user.username),
                    create_button("Activate", on_click=lambda e, user=user: self.activate_user(user.user_id))
                ]) for user in users
            ])

    def activate_user(self, user_id):
        self.db.activate_user(user_id)
        self.update_inactive_users_list()
        username = self.db.get_user(user_id).get_username()
        logger.info(f"User '{username}' has been activated by admin")

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
        self.project_name_field = TextField(
            label="Project Name",
            width=300,
            bgcolor=self.page.theme.color_scheme.background,
            color=self.page.theme.color_scheme.on_background
        )
        self.project_id_field = TextField(
            label="Project ID (Recommended: Leave blank for auto-generated)",
            width=300,
            bgcolor=self.page.theme.color_scheme.background,
            color=self.page.theme.color_scheme.on_background
        )

        self.select_members_column = Column()

        return Column(
            [
                Text(
                    "Create a New Project",
                    size=30,
                    color=self.page.theme.color_scheme.primary
                ),
                self.project_name_field,
                self.project_id_field,
                ElevatedButton(
                    "Next",
                    on_click=self.select_members
                ),
                ElevatedButton(
                    "Cancel",
                    on_click=self.cancel_dialog
                ),
                self.select_members_column
            ],
            scroll=ScrollMode.ALWAYS,
            expand=True,
            alignment=MainAxisAlignment.START,
            horizontal_alignment=CrossAxisAlignment.CENTER
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

        current_user_id = self.db.get_user_by_username(self.username).get_id()
        active_users = [user for user in active_users if user.get_id() != current_user_id]

        for user in active_users:
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        self.select_members_column.controls = [
            Text(
                f"Select members for project '{project_name}':",
                size=30,
                color=self.page.theme.color_scheme.primary
            ),
            Column(self.member_checkboxes),
            ElevatedButton(
                "Done",
                on_click=self.create_project_confirm,
                bgcolor=self.page.theme.color_scheme.secondary,
                color=self.page.theme.color_scheme.on_secondary
            ),
            ElevatedButton(
                "Cancel",
                on_click=lambda e: self.page.go("/create_project"),
                bgcolor=self.page.theme.color_scheme.secondary,
                color=self.page.theme.color_scheme.on_secondary
            )
        ]
        self.update()

    def create_project_confirm(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        if not selected_user_ids:
            self.show_snackbar("Please select at least one member!")
            return

        leader_id = self.db.get_user_by_username(self.username).get_id()
        self.db.add_project(self.get_new_project_id(), self.get_new_project_name(), leader_id, selected_user_ids)

        self.show_snackbar(f"Project '{self.get_new_project_name()}' created successfully!")

        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()
        logger.info(f"User '{self.username}' created project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'.")

    def cancel_dialog(self, e):
        self.page.go("/main")
        self.page.update()
        logger.info(f"User '{self.username}' canceled the creation of a new project.")

    def show_snackbar(self, message):
        snackbar = SnackBar(
            content=Text(message, color=self.page.theme.color_scheme.on_primary),
            bgcolor=self.page.theme.color_scheme.primary
        )
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
    def create_project_confirm(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        if not selected_user_ids:
            self.show_snackbar("Please select at least one member!")
            return

        leader_id = self.db.get_user_by_username(self.username).get_id()
        self.db.add_project(self.get_new_project_id(), self.get_new_project_name(), leader_id, selected_user_ids)

        self.show_snackbar(f"Project '{self.get_new_project_name()}' created successfully!")

   
        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()
        logger.info(f"User '{self.username}' created project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'.")

    def cancel_dialog(self, e):
        self.page.go("/create_project")
        self.page.go("/main")
        self.page.update()
        self.logger.info(f"User '{self.username}' canceled the creation of a new project.")
 

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
                    ElevatedButton("Back",on_click=lambda e: self.page.go("/main"))
                ]
            else:
                buttons = [
                    ElevatedButton("See Project Members", on_click=self.show_members),
                    ElevatedButton("See Tasks", on_click=self.show_tasks),
                    ElevatedButton("Back", on_click=lambda e: self.page.go("/main"))
                ]

            logger.info(f"User '{self.username}' viewed project '{project.get_project_name()}'.")

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
         logger.info(f"User '{self.username}' viewed project members for project ID '{self.project_id}'.")



    def add_task(self, e):
        add_task = AddTaskWindow(self.db, self.project_id, self.page)
        self.page.go(f"/add_task/{self.project_id}")
        self.page.update()
        logger.info(f"User '{self.username}' initiated adding a task for project ID '{self.project_id}'.")


    def show_tasks(self, e):
        show_tasks = ShowTasksWindow(self.db, self.project_id, self.page)
        self.page.go(f"/show_tasks/{self.project_id}")
        self.page.update()
        logger.info(f"User '{self.username}' viewed tasks for project ID '{self.project_id}'.")
  

        


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
        for status in Status:
            task_list = tasks_by_status.get(status, [])
            if not task_list:
                continue

            task_data_rows = []

            for task in sorted(task_list, key=lambda task: task.get_priority(), reverse=False):
                assignees = ", ".join([self.db.get_user_by_id(assignee_id).get_username() for assignee_id in task.get_assignees()])
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
                ft.Text(f"{status.value} Tasks", size=20),
                task_data_table
            ]))

        return ft.Column([
            ft.Text(f"Tasks of Project '{project.get_project_name()}'", size=30),
            *task_controls,
            create_button("Back", on_click=lambda e: self.page.go(f"/project_management/{self.project_id}"))
        ])

    def group_tasks_by_status(self, tasks):
        tasks_by_status = {status: [] for status in Status}
        for task in tasks:
            status = task.get_status()
            tasks_by_status[status].append(task)
        return tasks_by_status

    def show_task_details(self, task_id):
        show_task_details = ShowTaskDetailsWindow(self.db, task_id, self.page)
        self.page.go(f"/show_task_details/{task_id}")
        self.page.update()
        logger.info(f"User '{self.db.get_current_user_username(self.page)}' viewed details of task ID '{task_id}'.")

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
            Text(f"Description: {task.description}"),
            Text(f"Priority: {task.priority.name}"),
            Text(f"Status: {task.status.name}"),
            Text(f"Start Date: {task.start_datetime}"),
            Text(f"End Date: {task.end_datetime}"),
            Text(f"Assignees: {', '.join([self.db.get_user_by_id(assignee_id).get_username() for assignee_id in task.get_assignees()])}"),
            create_button("Show Comments", on_click=lambda e: self.show_comments(task_id)),
            create_button("Show History", on_click=lambda e: self.show_history(task_id)),
        ]

        assinee_names =[]
        for task_assignee in task.get_assignees():
              assinee_names.append( self.db.get_user_by_id(task_assignee).get_username())
        if self.db.get_current_user(self.page).get_username() in assinee_names:
            task_details_controls.append(create_button("Change Status", on_click=lambda e: self.change_task_status(task_id)))

        if self.db.get_current_user_id(self.page) == project.get_leader_id():
            task_details_controls.append(create_button("Change Priority", on_click=lambda e: self.change_task_priority(task_id)))
            task_details_controls.append(create_button("Add Assignees", on_click=lambda e: self.add_assignees(task_id)))
            task_details_controls.append(create_button("Remove Assignees", on_click=lambda e: self.remove_assignees(task_id)))

        task_details_controls.append(create_button("Back", on_click=lambda e: self.cancel_dialog()))

        return ft.Column([
            ft.Text(f"Task: {task.get_title()} for Project: {project.get_project_name()}", size=30),
            *task_details_controls
        ])

    def add_assignees(self, task_id):
        add_assignees = AddAssigneesWindow(self.db, task_id, self.page)
        self.page.go(f"/add_assignees/{task_id}")
        self.page.update()

    def remove_assignees(self, task_id):
        remove_assignees = RemoveAssigneesWindow(self.db, task_id, self.page)
        self.page.go(f"/remove_assignees/{task_id}")
        self.page.update()

    def change_task_status(self, task_id):
        change_task_status = ChangeStatusWindow(self.db, task_id, self.page)
        self.page.go(f"/change_task_status/{task_id}")
        self.page.update()

    def change_task_priority(self, task_id):
        change_task_priority = ChangePriorityWindow(self.db, task_id, self.page)
        self.page.go(f"/change_task_priority/{task_id}")
        self.page.update()

    def show_comments(self, task_id):
        show_comments = ShowCommentWindow(self.db, task_id, self.page)
        self.page.go(f"/show_comments/{task_id}")
        self.page.update()
        logger.info(f"User '{self.db.get_current_user_username(self.page)}' viewed comments for task ID '{task_id}'.")

    def show_history(self, task_id):
        show_history = ShowHistoryWindow(self.db, task_id, self.page)
        self.page.go(f"/show_history/{task_id}")
        self.page.update()
        logger.info(f"User '{self.db.get_current_user_username(self.page)}' viewed history for task ID '{task_id}'.")

    def cancel_dialog(self):
        project_id = self.db.get_task(self.task_id).get_project_id()
        self.page.go(f"/show_tasks/{project_id}")
        self.page.update()

class ShowCommentWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page
        self.add_comment_field = ft.TextField(label="Add Comment:")

    def build(self):
        comments = self.db.get_task_comments(self.task_id)
        comment_boxes = self._build_comment_boxes(comments)
        
        return ft.Column([
            *comment_boxes,
            self.add_comment_field,
            create_button("Add Comment", on_click=self.add_comment),
            create_button("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
        ])

    def _build_comment_boxes(self, comments):
        if not comments:
            return [ft.Text("No comments yet.", size=20)]

        comment_boxes = []
        for comment in comments:
            author = comment.get_username()
            timestamp = comment.get_timestamp()
            content = comment.get_content()
            comment_box = ft.Container(
                content=ft.Column([
                    ft.Text(f"{author} commented :"),
                    ft.Text(f"{content}"),
                    ft.Text(f"at {timestamp}")
                ]),
                padding=10,
                border=ft.border.all(1),
                margin=ft.margin.only(bottom=10)
            )

            comment_boxes.append(comment_box)

        return comment_boxes

    def add_comment(self, e):
        comment_content = self.add_comment_field.value
        if comment_content:
            username = self.db.get_current_user_username(self.page)
            self.db.add_comment(self.task_id, username, comment_content)
            self.db.add_task_history(self.task_id, f"Added comment: '{comment_content}'", username)
            self.add_comment_field.value = ""
            self.refresh_comments()
            logger.info(f"User '{username}' added the comment '{comment_content}'  to task ID '{self.task_id}'.")

    def refresh_comments(self):
        comments = self.db.get_task_comments(self.task_id)
        comment_boxes = self._build_comment_boxes(comments)
        self.page.views[-1].controls = [
            *comment_boxes,
            self.add_comment_field,
            create_button("Add Comment", on_click=self.add_comment),
            create_button("Back", on_click=self.go_back)
        ]
        show_comments = ShowCommentWindow(self.db, self.task_id, self.page)
        self.page.go(f"/show_comments/{self.task_id}")

    def go_back(self):
        show_task_details = ShowTaskDetailsWindow(self.db, self.task_id, self.page)
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

class ChangePriorityWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        priority_options = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]
        task = self.db.get_task(self.task_id)
        current_priority = task.get_priority().name

        self.priority_dropdown = ft.Dropdown(
            label="Priority",
            options=[ft.dropdown.Option(text=priority.name) for priority in priority_options],
            value=current_priority
        )

        return ft.Column([
            ft.Text(f"Change Priority for Task '{task.get_title()}'", size=20),
            self.priority_dropdown,
            create_button("Save", on_click=self.save_priority),
            create_button("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
        ])

    def save_priority(self, e):
        task = self.db.get_task(self.task_id)
        current_priority = task.get_priority()
        new_priority_value = self.priority_dropdown.value
        new_priority = Priority[new_priority_value]

        if current_priority != new_priority:
            self.db.change_priority(self.task_id, new_priority)
            self.db.add_task_history(
                self.task_id,
                f"Changed priority from {current_priority.name} to {new_priority.name}",
                self.db.get_current_user_username(self.page)
            )

        username = self.db.get_current_user_username(self.page)
        logger.info(f"User '{username}' changed priority of task '{task.get_title()}' from '{current_priority.name}' to '{new_priority.name}'.")

        self.page.dialog = None
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Priority changed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/show_task_details/{self.task_id}")

class ChangeStatusWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page
        self.status_dropdown = None

    def build(self):
        task = self.db.get_task(self.task_id)

        self.status_dropdown = ft.Dropdown(
            label="Change Task Status",
            options=[ft.dropdown.Option(status.value) for status in Status],
            value=task.get_status().value
        )

        return ft.Column([
            self.status_dropdown,
            create_button("Save", on_click=self.save_status),
            create_button("Back", on_click=self.go_back)
        ])

    def save_status(self, e):
        task = self.db.get_task(self.task_id)
        current_status = task.get_status()
        new_status = self.status_dropdown.value
        self.db.change_status(self.task_id, new_status)
        self.db.add_task_history(
                self.task_id, 
                f"Changed status from {current_status} to {new_status}", 
                self.db.get_current_user_username(self.page)
            )
        
        username = self.db.get_current_user_username(self.page) 
        logger.info(f"User '{username}' changed priority of task '{task.get_title()}' from '{current_status}' to '{new_status}'.")
        self.page.dialog = None
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Status changed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/show_task_details/{self.task_id}")

    def go_back(self, e):
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

class ShowHistoryWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        task = self.db.get_task(self.task_id)
        history_entries = self.db.get_task_history(self.task_id)

        history_controls = []
        if not history_entries:
            history_controls.append(ft.Text("No history yet.", size=20))
        else:
            for history in history_entries:
                history_controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(f"{history.get_author()}", size=14),
                            ft.Text(f"{history.get_action()}", size=16),
                            ft.Text(f"at: {history.get_timestamp()}", size=12),
                        ]),
                        padding=10,
                        border=ft.border.all(1),
                        margin=ft.margin.only(bottom=10)
                    )
                )

        return ft.Column([
            ft.Text(f"History of Task '{task.get_title()}'", size=30),
            *history_controls,
            create_button("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
        ])

class AddAssigneesWindow(UserControl):
    def __init__(self, db, task_id, page):
        super().__init__()
        self.db = db
        self.task_id = task_id
        self.page = page

    def build(self):
        project_id = self.db.get_task(self.task_id).get_project_id()
        active_users = self.db.get_project_member_ids(self.db.get_task(self.task_id).get_project_id())
        active_users.append(self.db.get_project(project_id).get_leader_id())

        current_assignees = self.db.get_task_assignees(self.task_id)

        self.member_checkboxes = []
        for user_id in active_users:
            if user_id not in current_assignees:
                cb = Checkbox(label=self.db.get_user_by_id(user_id).get_username(), key=user_id)
                self.member_checkboxes.append(cb)

        return Column([
            Text("Add Assignees to Task", size=30),
            Column(self.member_checkboxes),
            create_button("Save", on_click=self.save_assignees),
            create_button("Cancel", on_click=self.cancel_dialog)
        ])

    def save_assignees(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        task = self.db.get_task(self.task_id)
        for user_id in selected_user_ids:
            task.assign_user(user_id, self.db.get_current_user_username(self.page))
            self.db.add_assignee(self.task_id, user_id)
            self.db.add_task_history(self.task_id, f"Assigned user {self.db.get_user_by_id(user_id).get_username()}", self.db.get_current_user_username(self.page))
            logger.info(f"User '{self.db.get_user_by_id(user_id).get_username()}' assigned to task '{task.get_title()}' by user '{self.db.get_current_user_username(self.page)}'.")
        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Assignees added successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.go(f"/show_task_details/{self.task_id}")
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
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        return Column([
            Text("Remove Assignees from Task", size=30),
            Column(self.member_checkboxes),
            create_button("Save", on_click=self.remove_assignees),
            create_button("Cancel", on_click=self.cancel_dialog)
        ])

    def remove_assignees(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        task = self.db.get_task(self.task_id)
        for user_id in selected_user_ids:
            task.unassign_user(user_id, self.db.get_current_user_username(self.page))
            self.db.remove_assignee(self.task_id, user_id)
            self.db.add_task_history(self.task_id, f"Unassigned user {self.db.get_user_by_id(user_id).get_username()}", self.db.get_current_user_username(self.page))
            logger.info(f"User '{self.db.get_user_by_id(user_id).get_username()}' unassigned from task '{task.get_title()}' by user '{self.db.get_current_user_username(self.page)}'.")
        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Assignees removed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

class ProjectMembersWindow(UserControl):
    def __init__(self, db, project_id, page):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self.page = page
        self.member_checkboxes = []
        self.non_member_checkboxes = []

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
                create_button("Remove Selected Members", on_click=self.remove_members),
                create_button("Add Members", on_click=self.show_non_members),
                create_button("Back", on_click=self.cancel_dialog)
            ])
        else:
            return Column([
                Text("Project Members", size=30),
                Column(self.member_checkboxes),
                create_button("Back", on_click=self.cancel_dialog)
            ])

    def show_non_members(self, e):
      #  project_members = self.db.get_project_members(self.project_id)

        member_ids = self.db.get_project_member_ids(self.project_id)
        active_users = self.db.get_all_active_users()
        self.non_member_checkboxes.clear()

        for user in active_users:
            if user.get_id() not in member_ids and user.get_id() != self.db.get_project(self.project_id).get_leader_id():
                cb = Checkbox(label=user.get_username(), key=user.get_id())
                self.non_member_checkboxes.append(cb)

        self.page.views.append(
            ft.View(
                "/add_members",
                [
                    Column([
                        Text("Add Members", size=30),
                        Column(self.non_member_checkboxes),
                        create_button("Add Selected Members", on_click=self.add_members),
                        create_button("Cancel", on_click=self.cancel_add_members)
                    ])
                ]
            )
        )
        self.page.update()

    def add_members(self, e):
        selected_user_ids = [cb.key for cb in self.non_member_checkboxes if cb.value]

        for user_id in selected_user_ids:
            self.db.add_project_member(self.project_id, user_id)
            logger.info(f"User '{self.db.get_user_by_id(user_id).get_username()}' added to project '{self.project_id}' by user '{self.db.get_current_user_username(self.page)}'.")

        self.page.snack_bar = ft.SnackBar(content=ft.Text("Members added successfully!"))
        self.page.snack_bar.open = True
        self.update_member_checkboxes()
        self.page.go(f"/project_members/{self.project_id}")
        self.page.update()

    def remove_members(self, e):
        selected_member_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        for member_id in selected_member_ids:
            self.db.remove_project_member(self.project_id, member_id)
            project_tasks = self.db.get_project_tasks(self.project_id)
            for task in project_tasks:
                self.db.remove_assignee(task.get_task_id(), member_id)
                self.db.add_task_history(task.get_task_id(), f"Unassigned user {self.db.get_user_by_id(member_id).get_username()} due to removal from project", self.db.get_current_user_username(self.page))
        logger.info(f"User '{self.db.get_user_by_id(member_id).get_username()}' removed from project '{self.project_id}' by user '{self.db.get_current_user_username(self.page)}'.")
        self.update_member_checkboxes()
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Members removed and unassigned from tasks successfully!"))
        self.page.snack_bar.open = True
        self.page.go(f"/project_members/{self.project_id}")
        self.page.update()

    def update_member_checkboxes(self):
        project_members = self.db.get_project_members(self.project_id)
        self.member_checkboxes.clear()

        for member in project_members:
            cb = Checkbox(label=member.get_username(), key=member.get_id(), value=False)
            self.member_checkboxes.append(cb)

        self.update()

    def cancel_dialog(self, e):
        self.page.go(f"/project_management/{self.project_id}")
        self.page.update()

    def cancel_add_members(self, e):
        self.page.views.pop()
        self.page.update()

class AddTaskWindow(UserControl):
    def __init__(self, db, project_id, page):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self.page = page
        self.start_date_error = None
        self.end_date_error = None

    def build(self):
        self.error_message = Text(value="", color=colors.RED)
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
            value="LOW"
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
            create_button("Save", on_click=self.save_task),
            create_button("Cancel", on_click=self.cancel_dialog),
            self.error_message
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
        if start_date and not self.is_valid_date(start_date):
            self.show_snackbar("Invalid start date format. Please use YYYY-MM-DD HH:MM:SS.")
            return False
        if end_date and not self.is_valid_date(end_date):
            self.show_snackbar("Invalid end date format. Please use YYYY-MM-DD HH:MM:SS.")
            return False

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

        self.db.add_task(new_task)
        task_id = new_task.get_task_id()
        self.db.add_task_history(task_id, f"Created '{new_task.get_title()}' task", self.db.get_current_user_username(self.page))
        logger.info(f"New task '{new_task.get_title()}' added to project {self.project_id} by user '{self.db.get_current_user_username(self.page)}'.")
        for assignee_id in selected_assignees:
            username = self.db.get_user_by_id(assignee_id).get_username()
            self.db.add_task_history(task_id, f"Assigned user {username} to task", self.db.get_current_user_username(self.page))
            logger.info(f"User {username} assigned to task '{new_task.get_title()}' by user '{self.db.get_current_user_username(self.page)}'.")
        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Task added successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/project_management/{self.project_id}")
        self.page.update()

    def cancel_dialog(self, e):
        self.page.go(f"/project_management/{self.project_id}")
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

    # Light theme
    light_theme = ft.Theme(
        font_family="Custom fonts",
        color_scheme=ft.ColorScheme(
            primary=ft.colors.TEAL_ACCENT_700,
            background=ft.colors.TEAL_50,
            on_primary=ft.colors.BLACK,
            primary_container=ft.colors.PINK,
            on_primary_container=ft.colors.YELLOW,
            secondary=ft.colors.GREEN,
            on_background=ft.colors.BLACK,
            on_secondary=ft.colors.BLACK,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=ft.colors.BLACK),
            headline_large=ft.TextStyle(color=ft.colors.BLACK),
            title_medium=ft.TextStyle(color=ft.colors.BLACK),
            body_large=ft.TextStyle(color=ft.colors.BLACK),
            body_small=ft.TextStyle(color=ft.colors.BLACK),
            display_large=ft.TextStyle(color=ft.colors.BLACK),
            display_medium=ft.TextStyle(color=ft.colors.BLACK),
            display_small=ft.TextStyle(color=ft.colors.BLACK),
            headline_medium=ft.TextStyle(color=ft.colors.BLACK),
            headline_small=ft.TextStyle(color=ft.colors.BLACK),
            label_large=ft.TextStyle(color=ft.colors.BLACK),
            label_medium=ft.TextStyle(color=ft.colors.BLACK),
            label_small=ft.TextStyle(color=ft.colors.BLACK),
            title_large=ft.TextStyle(color=ft.colors.BLACK),
            title_small=ft.TextStyle(color=ft.colors.BLACK)
        )
    )

    # Dark theme
    dark_theme = ft.Theme(
        font_family="Custom fonts",
        # bottom_appbar_theme=BottomAppBarTheme(color=ft.colors.PINK),
        color_scheme=ft.ColorScheme(
            primary=ft.colors.PURPLE,
            background=ft.colors.BLACK,
            on_primary=ft.colors.WHITE,
            primary_container=ft.colors.WHITE,
            on_primary_container=ft.colors.WHITE,
            secondary=ft.colors.PURPLE_ACCENT,
            on_background=ft.colors.PURPLE_ACCENT,
            on_secondary=ft.colors.WHITE,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=ft.colors.WHITE),
            headline_large=ft.TextStyle(color=ft.colors.WHITE),
            title_medium=ft.TextStyle(color=ft.colors.WHITE),
            body_large=ft.TextStyle(color=ft.colors.WHITE),
            body_small=ft.TextStyle(color=ft.colors.WHITE),
            display_large=ft.TextStyle(color=ft.colors.WHITE),
            display_medium=ft.TextStyle(color=ft.colors.WHITE),
            display_small=ft.TextStyle(color=ft.colors.WHITE),
            headline_medium=ft.TextStyle(color=ft.colors.WHITE),
            headline_small=ft.TextStyle(color=ft.colors.WHITE),
            label_large=ft.TextStyle(color=ft.colors.WHITE),
            label_medium=ft.TextStyle(color=ft.colors.WHITE),
            label_small=ft.TextStyle(color=ft.colors.WHITE),
            title_large=ft.TextStyle(color=ft.colors.WHITE),
            title_small=ft.TextStyle(color=ft.colors.WHITE)
        )
    )

    # Apply the light theme initially
    page.theme = light_theme
    page.update()

    def switch_theme(e):
        if page.theme == light_theme:
            page.theme = dark_theme
        else:
            page.theme = light_theme
        page.update()
        update_views_theme()  # Ensure all views are updated

    def update_views_theme():
        # This function will update the views to match the current theme
        for view in page.views:
            if isinstance(view, ft.View):
                view.bgcolor = page.theme.color_scheme.background
                for container in view.controls:
                    if isinstance(container, ft.Container):
                        container.bgcolor = page.theme.color_scheme.background
                        container.update()
            view.update()
        page.update()


    def route_change(route):
        page.views.clear()

        def create_common_container(content):
            return ft.Container(
                content=content,
                bgcolor=page.theme.color_scheme.background,
                # width=1000,
                theme_mode=ThemeMode.DARK
            )

        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        create_common_container(
                            ft.Column(
                                [
                                    ft.Text("Do you want to login or sign up?", size=40),
                                    create_button("Login", lambda e: page.go("/login")),
                                    create_button("Sign Up", lambda e: page.go("/signup")),
                                    create_button("Switch Theme", switch_theme),
                                    create_button("Exit", lambda e: page.window_destroy()),
                                ],
                            )
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/login":
            page.views.append(
                ft.View(
                    "/login",
                    [
                        create_common_container(
                            ft.Column(
                                [LoginPage(db, on_login=lambda username: on_login(page, username))],
                            )
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/signup":
            page.views.append(
                ft.View(
                    "/signup",
                    [
                        create_common_container(
                            ft.Column(
                                [SignupPage(db, on_signup=lambda username: on_signup(page, username))],
                            )
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/main":
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    "/main",
                    [
                        ft.Container(
                            content=ft.Column(
                                [MainPage(db, username, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/projects_list":
            page.views.append(
                ft.View(
                    "/projects_list",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ProjectListPage(db, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/manage_users":
            page.views.append(
                ft.View(
                    "/manage_users",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ManageUsersPage(db)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/active_users":
            page.views.append(
                ft.View(
                    "/active_users",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ActiveUsersPage(db)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/inactive_users":
            page.views.append(
                ft.View(
                    "/inactive_users",
                    [
                        ft.Container(
                            content=ft.Column(
                                [InactiveUsersPage(db)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route == "/create_project":
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    "/create_project",
                    [
                        ft.Container(
                            content=ft.Column(
                                [CreateProjectPage(db, username, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/project_management"):
            project_id = page.route.split("/")[-1]
            username = page.session.get("username")
            page.views.append(
                ft.View(
                    f"/project_management/{project_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ProjectManagementPage(db, username, project_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/add_task"):
            project_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/add_task/{project_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [AddTaskWindow(db, project_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/project_members"):
            project_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/project_members/{project_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ProjectMembersWindow(db, project_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/show_tasks"):
            project_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/show_tasks/{project_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ShowTasksWindow(db, project_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/show_task_details"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/show_task_details/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ShowTaskDetailsWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/add_assignees"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/add_assignees/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [AddAssigneesWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/remove_assignees"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/remove_assignees/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [RemoveAssigneesWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/show_history"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/show_history/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ShowHistoryWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/show_comments"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/show_comments/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ShowCommentWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/change_task_status"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/change_task_status/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ChangeStatusWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
                )
            )
        elif page.route.startswith("/change_task_priority"):
            task_id = page.route.split("/")[-1]
            page.views.append(
                ft.View(
                    f"/change_task_priority/{task_id}",
                    [
                        ft.Container(
                            content=ft.Column(
                                [ChangePriorityWindow(db, task_id, page)],
                            ),
                            bgcolor=page.theme.color_scheme.background
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background
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

