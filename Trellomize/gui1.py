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
            Text("Dont have an account?!", size=14),
            ElevatedButton("Sign Up", on_click=self.show_signup),
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
            Text("Already have an account?!", size=14),
            ElevatedButton("Login", on_click=self.show_login),
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
        elif not username or not email or not password :
            self.error_message.value = "Invalid input!"
        elif not self.check_email(email) or not password:
            self.error_message.value = "Invalid email address!"
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
            ElevatedButton("Create Project", on_click=self.create_project),
            ElevatedButton("Show Projects", on_click=self.show_projects)
        ]

        if self.db.is_admin(self.username):
            buttons.append(ElevatedButton("Manage Users", on_click=self.manage_users))

        return Column([
            Text(f"Welcome, {self.username}!", size = 20),
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
        if not leader_projects:
            leader_controls.append(Text("No projects found.", italic=True))
       
        member_controls = []
        for project in member_projects:
            member_controls.append(Row([
                Text(project.get_project_name()),
                ElevatedButton("Manage", on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id))
            ]))
        if not member_projects:
            member_controls.append(Text("No projects found.", italic=True))

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
            ElevatedButton("Back", on_click=lambda e: self.page.go("/main")) 
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
            ElevatedButton("Cancel",  on_click=self.cancel_dialog)
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
        self.page.update()
        # main = MainPage(self.db,self.username,self.page)
        # self.page.go(f"/main")
        # self.page.update()

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
       for status in Status:
           task_list = tasks_by_status.get(status, [])
           if not task_list:
               continue  # Skip this status if there are no tasks
   
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
           ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/project_management/{self.project_id}"))
       ])
    
    def group_tasks_by_status(self, tasks):
        tasks_by_status = {status: [] for status in Status}
        for task in tasks:
            status = task.get_status()
            tasks_by_status[status].append(task)
        return tasks_by_status



    def show_task_details(self, task_id):
        show_task_details = ShowTaskDetailsWindow(self.db, task_id , self.page)
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
            Text(f"Assignees: {', '.join([ self.db.get_user_by_id(assignee_id).get_username() for assignee_id in task.get_assignees()])}"),
            ElevatedButton("Show Comments", on_click=lambda e: self.show_comments(task_id)),
            ElevatedButton("Show History", on_click=lambda e: self.show_history(task_id)),
           # ElevatedButton("Back", on_click=lambda e: self.close_window())
        ]
       
        assinee_names =[]
        for task_assignee in task.get_assignees():
              assinee_names.append( self.db.get_user_by_id(task_assignee).get_username())
        if self.db.get_current_user(self.page).get_username() in assinee_names:
            task_details_controls.append(ElevatedButton("Change Status", on_click=lambda e: self.change_task_status(task_id)))

        if self.db.get_current_user_id(self.page) == project.get_leader_id():
            task_details_controls.append(ElevatedButton("Change Priority", on_click=lambda e: self.change_task_priority(task_id)))
            task_details_controls.append(ElevatedButton("Add Assignees", on_click=lambda e: self.add_assignees(task_id)))
            task_details_controls.append(ElevatedButton("Remove Assignees", on_click=lambda e: self.remove_assignees(task_id)))
        
        task_details_controls.append(ElevatedButton("Back", on_click=lambda e: self.close_window()))

        return ft.Column([           
            ft.Text(f"Task: {task.get_title()} for Project: {project.get_project_name()}", size=30),  # Show project name
            *task_details_controls])

    def add_assignees(self,task_id):
        add_assignees = AddAssigneesWindow(self.db, task_id , self.page)
        self.page.go(f"/add_assignees/{task_id}")
        self.page.update()

    def remove_assignees(self,task_id):
        remove_assignees = RemoveAssigneesWindow(self.db, task_id , self.page)
        self.page.go(f"/remove_assignees/{task_id}")
        self.page.update()

    def change_task_status(self,task_id):
        change_task_status = ChangeStatusWindow(self.db, task_id , self.page)
        self.page.go(f"/change_task_status/{task_id}")
        self.page.update()

    def change_task_priority(self,task_id):
        change_task_priority = ChangePriorityWindow(self.db, task_id , self.page)
        self.page.go(f"/change_task_priority/{task_id}")
        self.page.update()

    def show_comments(self,task_id):
        show_comments = ShowCommentWindow(self.db, task_id , self.page)
        self.page.go(f"/show_comments/{task_id}")
        self.page.update()

    def show_history(self,task_id):
        show_history = ShowHistoryWindow(self.db, task_id , self.page)
        self.page.go(f"/show_history/{task_id}")
        self.page.update()


    def close_window(self):
        self.page.close_dialog()



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
        add_comment_button = ft.ElevatedButton("Add Comment", on_click=self.add_comment)
        
        return ft.Column([
            *comment_boxes,
            self.add_comment_field,
            add_comment_button,
            ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
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

    def refresh_comments(self):
        comments = self.db.get_task_comments(self.task_id)
        comment_boxes = self._build_comment_boxes(comments)
        self.page.views[-1].controls = [
            *comment_boxes,
            self.add_comment_field,
            ft.ElevatedButton("Add Comment", on_click=self.add_comment),
            ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
        ]
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
            ft.ElevatedButton("Save", on_click=self.save_priority),
            ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
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

        self.page.dialog = None
        self.page.snack_bar = SnackBar(content=Text("Priority changed successfully!"))
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
            value=task.get_status().value  # Set the current status as the default value
        )

        return ft.Column([
            self.status_dropdown,
            ft.ElevatedButton("Save", on_click=self.save_status),
            ft.ElevatedButton("Back", on_click=self.go_back)
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
        self.page.dialog = None
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Status changed successfully!"))
        self.page.snack_bar.open = True
        self.page.update()
        self.page.go(f"/show_task_details/{self.task_id}")
        self.page.update()

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
            ft.ElevatedButton("Back", on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"))
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
       # active_usernames = [user.get_username() for user in active_users]

        current_assignees = self.db.get_task_assignees(self.task_id)

       # current_usernames =[user.get_username() for user in current_assignees]
      #  current_user_id = self.db.get_current_user_id(self.page)
       # options = [username for username in active_usernames if username not in current_usernames ]

        self.member_checkboxes = []
        for user_id in active_users : 
            if user_id not in current_assignees :
               cb = Checkbox(label=self.db.get_user_by_id(user_id).get_username(), key=user_id)
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
            task.assign_user(user_id,self.db.get_current_user_username(self.page))
            self.db.add_assignee(self.task_id , user_id)
            self.db.add_task_history(self.task_id, f"Assigned user {self.db.get_user_by_id(user_id).get_username()}", self.db.get_current_user_username(self.page))

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
            ElevatedButton("Save", on_click=self.remove_assignees),
            ElevatedButton("Cancel", on_click=self.cancel_dialog)
        ])

    def remove_assignees(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]

        task = self.db.get_task(self.task_id)
        for user_id in selected_user_ids:
            task.unassign_user(user_id ,self.db.get_current_user_username(self.page) )
            self.db.remove_assignee(self.task_id,user_id)
            self.db.add_task_history(self.task_id, f"Unassigned user {self.db.get_user_by_id(user_id).get_username()}", self.db.get_current_user_username(self.page))

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


# class AddTaskWindow(UserControl):
#     def __init__(self, db, project_id, page):
#         super().__init__()
#         self.db = db
#         self.project_id = project_id
#         self.page = page
#         self.title_error = None
#         self.description_error = None
#         self.start_date_error = None
#         self.end_date_error = None

#     def build(self):
#         self.title_field = TextField(label="Title")
#         self.description_field = TextField(label="Description")
#         self.priority_dropdown = Dropdown(
#             label="Priority",
#             options=[
#                 ft.dropdown.Option("CRITICAL"),
#                 ft.dropdown.Option("HIGH"),
#                 ft.dropdown.Option("MEDIUM"),
#                 ft.dropdown.Option("LOW")
#             ],
#             value="LOW"  # Default value for priority
#         )
#         self.start_date_field = TextField(label="Start Date (YYYY-MM-DD HH:MM:SS)")
#         self.end_date_field = TextField(label="End Date (YYYY-MM-DD HH:MM:SS)")
#         self.member_checkboxes = []
#         self.choose_assignees_label = Text("Choose Assignees:")

#         active_users = self.db.get_project_members(self.project_id)
#         active_users.append(self.db.get_user_by_id(self.db.get_project(self.project_id).get_leader_id()))
#         for user in active_users:
#             cb = Checkbox(label=user.get_username(), key=user.get_id())
#             self.member_checkboxes.append(cb)

#         return Column([
#             Text("Add a New Task", size=30),
#             self.title_field,
#             self._create_error_text(self.title_error),
#             self.description_field,
#             self._create_error_text(self.description_error),
#             self.priority_dropdown,
#             self.start_date_field,
#             self._create_error_text(self.start_date_error),
#             self.end_date_field,
#             self._create_error_text(self.end_date_error),
#             self.choose_assignees_label,
#             Column(self.member_checkboxes),
#             ElevatedButton("Save", on_click=self.save_task),
#             ElevatedButton("Cancel", on_click=self.cancel_dialog)
#         ])

#     def _create_error_text(self, error_message):
#         if error_message:
#             return Text(error_message, color="red")
#         return Container()  # Empty container if there's no error

#     def validate_fields(self):
#         title = self.title_field.value
#         description = self.description_field.value
#         start_date = self.start_date_field.value
#         end_date = self.end_date_field.value

#         self.title_error = None
#         self.description_error = None
#         self.start_date_error = None
#         self.end_date_error = None

#         if not title:
#             self.title_error = "Title field cannot be empty."
#         if not description:
#             self.description_error = "Description field cannot be empty."
#         if start_date and not self.is_valid_date(start_date):
#             self.start_date_error = "Invalid start date format. Please use YYYY-MM-DD HH:MM:SS."
#         if end_date and not self.is_valid_date(end_date):
#             self.end_date_error = "Invalid end date format. Please use YYYY-MM-DD HH:MM:SS."

#         if self.title_error or self.description_error or self.start_date_error or self.end_date_error:
#             self.update()  # Update the UI to show errors
#             return False
#         return True

#     def save_task(self, e):
#         if not self.validate_fields():
#             return

#         start_date = self.start_date_field.value
#         end_date = self.end_date_field.value

#         if not start_date:
#             start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         if not end_date:
#             end_date = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

#         selected_assignees = [cb.key for cb in self.member_checkboxes if cb.value]

#         # Create a new Task object
#         new_task = Task(
#             project_id=self.project_id,
#             title=self.title_field.value,
#             description=self.description_field.value,
#             priority=self.priority_dropdown.value,
#             status="BACKLOG",
#             assignees=selected_assignees,
#             start_datetime=self.parse_date(start_date),
#             end_datetime=self.parse_date(end_date)
#         )

#         # Add the task to the database
#         task_id = self.db.add_task(new_task)

#         # Add task creation to the history
#         self.db.add_task_history(task_id, f"Task '{new_task.get_title()}' created", self.db.get_current_user_username(self.page))

#         # Add assignee assignment to the history
#         for assignee_id in selected_assignees:
#             username = self.db.get_user_by_id(assignee_id).get_username()
#             self.db.add_task_history(task_id, f"Assigned user {username} to task", self.db.get_current_user_username(self.page))

#         # Close the dialog and show a success message
#         self.page.dialog = None
#         self.page.snack_bar = SnackBar(content=Text("Task added successfully!"))
#         self.page.snack_bar.open = True
#         self.page.update()
#         self.page.go(f"/project_management/{self.project_id}")
#         self.page.update()

#     def cancel_dialog(self, e):
#         self.page.dialog = None
#         self.page.update()

#     def is_valid_date(self, date_string):
#         try:
#             datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
#             return True
#         except ValueError:
#             return False

#     def parse_date(self, date_string):
#         return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

#     def show_snackbar(self, message):
#         snackbar = ft.SnackBar(content=ft.Text(message))
#         self.page.snack_bar = snackbar
#         self.page.snack_bar.open = True
#         self.page.update()

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
            ElevatedButton("Cancel", on_click=self.cancel_dialog),
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

        
        self.db.add_task(new_task)
        task_id = new_task.get_task_id()
        self.db.add_task_history(task_id, f"Created '{new_task.get_title()}' task", self.db.get_current_user_username(self.page))
        for assignee_id in selected_assignees:
            username = self.db.get_user_by_id(assignee_id).get_username()
            self.db.add_task_history(task_id, f"Assigned user {username} to task", self.db.get_current_user_username(self.page))

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

    

class ScrollablePage(ft.Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vertical_scroll = "auto"
        self.horizontal_scroll = "auto"

def main(page : ft.Page):
    db = Database()
   
    

    def route_change(route):
        ft.ScrollMode.AUTO
       # page.add(scroll_view)
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
            page.vertical_scroll = "auto"
            page.horizontal_scroll = "auto"
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
        elif page.route.startswith("/add_assignees"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/add_assignees/{task_id}",
                    [AddAssigneesWindow(db, task_id, page)],
                )
            )     
        elif page.route.startswith("/remove_assignees"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/remove_assignees/{task_id}",
                    [RemoveAssigneesWindow(db, task_id, page)],
                )
            )     
        elif page.route.startswith("/show_history"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/show_history/{task_id}",
                    [ShowHistoryWindow(db, task_id, page)],
                )
            )     
        elif page.route.startswith("/show_comments"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/show_comments/{task_id}",
                    [ShowCommentWindow(db, task_id, page)],
                )
            )     
        elif page.route.startswith("/change_task_status"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/change_task_status/{task_id}",
                    [ChangeStatusWindow(db, task_id, page)],
                )
            )   
        elif page.route.startswith("/change_task_priority"):
             task_id = page.route.split("/")[-1]
             page.views.append(
                ft.View(
                    f"/change_task_priority/{task_id}",
                    [ChangePriorityWindow(db, task_id, page)],
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
