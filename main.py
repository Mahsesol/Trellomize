import datetime
import hashlib
import logging
import re
import sqlite3
import sys
import uuid
from datetime import date, datetime, timedelta

import flet as ft
from flet import *
from history import History
from project import Project
from task import *
from user import User

from database import Database

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
   

def create_button(text, on_click, width=1000, height=50):
    return ft.ElevatedButton(
        text,
        on_click=on_click,
        width=width,
        height=height,
    )

class LoginPage(UserControl):
    def __init__(self, db, on_login=None):
        super().__init__()
        self.db = db
        self.on_login = on_login

    def build(self):
        self.username = TextField(
            label="Username",
            width=300,
            border_color=self.page.theme.color_scheme.on_primary,
            border_width=2,
            border_radius=10,
            bgcolor=self.page.theme.color_scheme.on_surface,
        )
        self.password = TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=self.page.theme.color_scheme.on_primary,
            border_width=2,
            border_radius=10,
            bgcolor=self.page.theme.color_scheme.on_surface,
        )
        self.error_message = Text(value="", color=self.page.theme.color_scheme.error, size=14)
        
        login_button = ElevatedButton(
            text="Login",
            on_click=self.login,
            width=150,
            style=ButtonStyle(
                bgcolor=self.page.theme.color_scheme.on_primary,
                color={"": colors.WHITE},
                shape=RoundedRectangleBorder(radius=10),
                padding=Padding(15, 10, 15, 10)
            )
        )
        
        signup_button = ElevatedButton(
            text="Sign Up",
            on_click=self.show_signup,
            width=150,
            style=ButtonStyle(
                bgcolor=self.page.theme.color_scheme.primary,
                color={"": colors.WHITE},
                shape=RoundedRectangleBorder(radius=10),
                padding=Padding(15, 10, 15, 10)
            )
        )
        
        return Container(
            content=Column(
                controls=[
                    Text("Login", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    self.username,
                    self.password,
                    login_button,
                    Text("Don't have an account?", size=14,  color=self.page.theme.color_scheme.on_secondary),
                    signup_button,
                    self.error_message
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20
        )

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
                logger.warning(f"Inactive account login attempt for user: '{username}'")

        else:
            self.error_message.value = "Invalid username or password!"
            logger.warning(f"Invalid login attempt for user: '{username}'")
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
        self.username = TextField(
            label="Username",
            width=300,
            border_color=self.page.theme.color_scheme.on_secondary,
            border_width=2,
            border_radius=10,
            bgcolor=self.page.theme.color_scheme.on_surface,
        )
        self.email = TextField(
            label="Email",
            width=300,
            border_color=self.page.theme.color_scheme.on_secondary,
            border_width=2,
            border_radius=10,
            bgcolor= self.page.theme.color_scheme.on_surface,
        )
        self.password = TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color=self.page.theme.color_scheme.on_secondary,
            border_width=2,
            border_radius=10,
            bgcolor=self.page.theme.color_scheme.on_surface,
        )
        self.confirm_password = TextField(
            label="Confirm Password",
            password=True,
            can_reveal_password=True,
            width=300,
            border_color= self.page.theme.color_scheme.on_secondary,
            border_width=2,
            border_radius=10,
            bgcolor=self.page.theme.color_scheme.on_surface,
        )
        self.error_message = Text(value="", color=colors.RED, size=14)

        signup_button = ElevatedButton(
            text="Sign Up",
            on_click=self.signup,
            width=150,
            style=ButtonStyle(
                bgcolor=self.page.theme.color_scheme.on_primary,
                color={"": colors.WHITE},
                shape=RoundedRectangleBorder(radius=10),
                padding=Padding(15, 10, 15, 10)
            )
        )

        login_button = ElevatedButton(
            text="Login",
            on_click=self.show_login,
            width=150,
            style=ButtonStyle(
                bgcolor=self.page.theme.color_scheme.primary,
                color={"": colors.WHITE},
                shape=RoundedRectangleBorder(radius=10),
                padding=Padding(15, 10, 15, 10)
            )
        )

        return Container(
            content=Column(
                controls=[
                    Text("Sign Up", size=30, weight=FontWeight.BOLD),
                    self.username,
                    self.email,
                    self.password,
                    self.confirm_password,
                    signup_button,
                    Text("Already have an account?", size=14,  color=self.page.theme.color_scheme.on_secondary),
                    login_button,
                    self.error_message
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20
        )

    def signup(self, e):
        username = self.username.value
        email = self.email.value
        password = self.password.value
        confirm_password = self.confirm_password.value

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
        elif password != confirm_password:
            print("password", password)
            print("confirm_password", confirm_password)
            self.error_message.value = "Passwords doesn't match"
            logger.warning(f"Signup attempt failed for user '{username}': Passwords doesn't match")
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
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        return bool(re.match(pat, email))

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
            ElevatedButton(
                text="Create Project",
                on_click=self.create_project,
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.on_primary_container,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            ),
            ElevatedButton(
                text="Show Projects",
                on_click=self.show_projects,
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.secondary,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            ),
            ElevatedButton(
                text="Log out",
                on_click=self.go_back,
                width=300,
                style=ButtonStyle(
                    bgcolor={"": colors.RED_ACCENT_700},
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            )
        ]

        if self.db.is_admin(self.username):
            buttons.append(
                ElevatedButton(
                    text="Manage Users",
                    on_click=self.manage_users,
                    width=300,
                    style=ButtonStyle(
                        bgcolor={"": colors.PURPLE_ACCENT_700},
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )

        return Container(
            content=Column(
                controls=[
                    Text(f"Welcome, {self.username}!", size=30, weight=FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary),
                    *buttons
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20
        )

    def create_project(self, e):
        create_project_page = CreateProjectPage(self.db, self.username, self.page)
        self.page.views.append(
            ft.View(
                "/create_project",
                [create_project_page],
                scroll=ScrollMode.AUTO,
                bgcolor=self.page.theme.color_scheme.background,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
        )
        self.page.update()
    def go_back(self,e):
        logger.info(f"User '{self.username}' logged out successfully!")
        self.page.go("/")

    def show_projects(self, e):
        logger.info(f"User '{self.username}' requested to see their projects")
        projects_list = ProjectListPage(self.db, self.page)
        self.page.go(f"/projects_list")
        self.page.update()

    def manage_users(self, e):
        self.page.go("/manage_users")

class ProjectListPage(UserControl):
    def __init__(self, db, page):
        super().__init__()
        self.db = db
        self.page = page
        self.username = self.db.get_current_user(self.page).get_username()
        self.user_id = self.db.get_current_user_id(self.page)

    def build(self):
        button_width = 300  # Set a fixed width for all buttons
        leader_projects = self.db.get_user_project_leader(self.user_id)
        member_projects = self.db.get_user_project_member(self.user_id)

        leader_controls = [
            Text(f"Projects you are the leader of, {self.username}:", size=20, weight=FontWeight.BOLD)
        ]
        for project in leader_projects:
            leader_controls.append(
                ElevatedButton(
                    text=f"Manage {project.get_project_name()}",
                    on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id),
                    width=button_width,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )
        if not leader_projects:
            leader_controls.append(Text("No projects found.", italic=True))

        member_controls = [
            Text(f"Projects you are a member of, {self.username}:", size=20, weight=FontWeight.BOLD)
        ]
        for project in member_projects:
            member_controls.append(
                ElevatedButton(
                    text=f"Manage {project.get_project_name()}",
                    on_click=lambda e, project_id=project.get_project_id(): self.manage_project(project_id),
                    width=button_width,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_primary_container,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )
        if not member_projects:
            member_controls.append(Text("No projects found.", italic=True))

        return Container(
            content=Column(
                controls=[
                    Text("Project List", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    *leader_controls,
                    *member_controls,
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go("/main"),
                        width=button_width,
                        style=ButtonStyle(
                            bgcolor={"": colors.RED_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20
        )

    def manage_project(self, project_id):
         project_management_page = ProjectManagementPage(self.db, self.username, project_id, self.page)
    
         self.page.views.append(
             ft.View(
                 "/project_management",
                 [
                     ft.Container(
                         content=project_management_page.build(),  
                         bgcolor=self.page.theme.color_scheme.background, 
                         expand=True
                     )
                 ],
                 bgcolor=self.page.theme.color_scheme.background,
                 scroll=ft.ScrollMode.ALWAYS,
            )
         )
         self.page.update()  
         self.page.go(f"/project_management/{project_id}")


class ManageUsersPage(UserControl):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def build(self):
        return Container(
            content=Column(
                controls=[
                    Text("User Management", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    self.create_user_button("Manage Active Users", self.page.theme.color_scheme.on_primary , self.show_active_users),
                    self.create_user_button("Manage Inactive Users", self.page.theme.color_scheme.primary , self.show_inactive_users),
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go("/main"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.on_primary_container,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def create_user_button(self, title, color, on_click):
        return ElevatedButton(
            text=title,
            on_click=on_click,
            width=300,
            style=ButtonStyle(
                bgcolor={"": color},
                color={"": colors.WHITE},
                shape=RoundedRectangleBorder(radius=10),
                padding=Padding(15, 10, 15, 10)
            )
        )

    def show_active_users(self, e):
        self.page.go("/active_users")

    def show_inactive_users(self, e):
        self.page.go("/inactive_users")

class ActiveUsersPage(UserControl):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def build(self):
        self.user_list = self.get_active_users_list()
        return Container(
            content=Column(
                controls=[
                    Text("Active Users", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    self.user_list,
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go("/manage_users"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.on_primary_container,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )
    
    def get_active_users_list(self):
        users = self.db.get_all_active_users()
        if not users:
            return Column([Text("No active users found")])
        else:
            return Column([
                Row([
                    Text(user.get_username()),
                    ElevatedButton(
                        text="Inactivate",
                        on_click=lambda e, user=user: self.inactivate_user(user.get_id()),
                        width=150,
                        style=ButtonStyle(
                            bgcolor={"": colors.RED_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(10, 5, 10, 5)
                        )
                    )
                ], alignment=MainAxisAlignment.CENTER, spacing=10) for user in users if not user.get_is_admin()
            ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)

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
        return Container(
            content=Column(
                controls=[
                    Text("Inactive Users", size=30, weight=FontWeight.BOLD, color=self.page.theme.color_scheme.on_background,),
                    self.user_list,
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go("/manage_users"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.on_primary_container, 
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def get_inactive_users_list(self):
        users = self.db.get_all_inactive_users()
        if not users:
            return Column([Text("No inactive users found")])
        else:
            return Column([
                Row([
                    Text(user.get_username()),
                    ElevatedButton(
                        text="Activate",
                        on_click=lambda e, user=user: self.activate_user(user.get_id()),
                        width=150,
                        style=ButtonStyle(
                            bgcolor={"": colors.GREEN_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(10, 5, 10, 5)
                        )
                    )
                ], alignment=MainAxisAlignment.CENTER, spacing=10) for user in users
            ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10)

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
            width=400,
            bgcolor=self.page.theme.color_scheme.background,
            color=self.page.theme.color_scheme.on_background,
            border_color=self.page.theme.color_scheme.primary,
            border_width=2,
            border_radius=10
        )
        self.project_id_field = TextField(
            label="Project ID (Optional)",
            width=400,
            bgcolor=self.page.theme.color_scheme.background,
            color=self.page.theme.color_scheme.on_background,
            border_color=self.page.theme.color_scheme.primary,
            border_width=2,
            border_radius=10
        )

        self.select_members_column = Column()

        return Column(
            [
                Text(
                    "Create a New Project",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=self.page.theme.color_scheme.primary
                ),
                self.project_name_field,
                self.project_id_field,
                Row(
                    [
                        ElevatedButton(
                            "Next",
                            on_click=self.select_members,
                            style=ButtonStyle(
                                color=self.page.theme.color_scheme.background,
                                bgcolor=self.page.theme.color_scheme.primary,
                                padding=Padding(15, 15, 15, 15),
                            )
                        ),
                        ElevatedButton(
                            "Cancel",
                            on_click=self.cancel_dialog,
                            style=ButtonStyle(
                                color=self.page.theme.color_scheme.background,
                                bgcolor=self.page.theme.color_scheme.secondary,
                                padding=Padding(15, 15, 15, 15),
                            )
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    width=400
                ),
                Divider(height=20, thickness=2, color=self.page.theme.color_scheme.primary),
                self.select_members_column
            ],
            scroll=ScrollMode.AUTO,
            alignment=MainAxisAlignment.START,
            horizontal_alignment=CrossAxisAlignment.CENTER,
        )

    def select_members(self, e):
        project_name = self.project_name_field.value
        project_id = self.project_id_field.value

        if not project_name:
            self.show_snackbar("Please enter a project name!")
            logger.warning(f"Attempt to create project failed : Project doesn't have a name")
            return

        if not project_id:
            project_id = str(uuid.uuid4())
        elif self.db.project_id_exist(project_id):
            self.show_snackbar("Project id already exist!")
            logger.warning(f"Attempt to create project failed : Project id '{project_id}' already exist")
            return

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
                weight=ft.FontWeight.BOLD,
                color=self.page.theme.color_scheme.primary
            ),
            Column(self.member_checkboxes, alignment=CrossAxisAlignment.CENTER),  # Center checkboxes
            Row(
                [
                    ElevatedButton(
                        "Done",
                        on_click=self.create_project_confirm,
                        style=ButtonStyle(
                            color=self.page.theme.color_scheme.background,
                            bgcolor=self.page.theme.color_scheme.primary,
                            padding=Padding(15, 15, 15, 15),
                        )
                    ),
                    ElevatedButton(
                        "Cancel",
                        on_click=self.cancel_select_members,
                        style=ButtonStyle(
                            color=self.page.theme.color_scheme.background,
                            bgcolor=self.page.theme.color_scheme.secondary,
                            padding=Padding(15, 15, 15, 15),
                        )
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,  # Center buttons
                spacing=20,  
            )
        ]
        self.update()

    def create_project_confirm(self, e):
        selected_user_ids = [cb.key for cb in self.member_checkboxes if cb.value]
        selected_usernames = [self.db.get_user_by_id(user_id).get_username() for user_id in selected_user_ids]


        # if not selected_user_ids:
        #     self.show_snackbar("Please select at least one member!")
        #     return

        leader_id = self.db.get_user_by_username(self.username).get_id()
        self.db.add_project(self.get_new_project_id(), self.get_new_project_name(), leader_id, selected_user_ids)

        self.show_snackbar(f"Project '{self.get_new_project_name()}' created successfully!")

        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()
        logger.info(f"User '{self.username}' created project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'.")
        for username in selected_usernames:
            logger.info(f"User '{username}' added to the project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'by user '{self.username}'.")

    def cancel_dialog(self, e):
        logger.info("Cancel button clicked - navigating to main page")
        self.page.go("/main")
        self.page.update()
        logger.info(f"User '{self.username}' canceled the creation of a new project.")

    def cancel_select_members(self, e):
        logger.info("Cancel button clicked in select members - navigating to create project")
        self.page.go("/create_project")
        self.page.update()

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
        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()
        logger.info(f"User '{self.username}' created project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'.")

    def cancel_dialog(self, e):
        self.page.go("/create_project")
        self.page.go("/main")
        self.page.update()
        logger.info(f"User '{self.username}' canceled the creation of a new project.")
 

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
        self.page.go(f"/project_management/{self.get_new_project_id()}")
        self.page.update()
        logger.info(f"User '{self.username}' created project '{self.get_new_project_name()}' with ID '{self.get_new_project_id()}'.")

    def cancel_dialog(self, e):
        self.page.go("/create_project")
        self.page.go("/main")
        self.page.update()
        logger.info(f"User '{self.username}' canceled the creation of a new project.")
 

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

        if project:
            is_leader = self.db.get_user_by_username(self.username).get_id() == project.get_leader_id()

            buttons = [
                ElevatedButton(
                    text="See Project Members",
                    on_click=self.show_members,
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                ),
                ElevatedButton(
                    text="See Tasks",
                    on_click=self.show_tasks,
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.primary_container,
                         color={"": colors.WHITE},
                         shape=RoundedRectangleBorder(radius=10),
                         padding=Padding(15, 10, 15, 10)
                    )
                ),
                ElevatedButton(
                    text="Back",
                    on_click=lambda e: self.page.go("/main"),
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            ]

            if is_leader:
                buttons.insert(1, ElevatedButton(
                    text="Add Task",
                    on_click=self.add_task,
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_primary_container,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                ))

            logger.info(f"User '{self.username}' viewed project '{project.get_project_name()}'.")
            self.page.bgcolor = self.page.theme.color_scheme.background
            
            return Container(
                content=Column(
                    controls=[
                        Text(f"Project: {project.get_project_name()}", size=30, weight=FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary),
                        *buttons
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=20,
                    expand=True
                ),
                alignment=ft.alignment.center,
                padding=20,
                bgcolor=self.page.theme.color_scheme.background,
                expand=True
            )
        else:
            logger.warning(f"Project with id '{self.project_id}' not found")
            return Container(
                content=Text("Project not found", size=30, color=colors.RED),
                alignment=ft.alignment.center,
                padding=20,
                bgcolor=self.page.theme.color_scheme.background,
                expand=True
            )

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
                    ft.DataCell(
                        ElevatedButton(
                            text="Details",
                            on_click=lambda e, task_id=task.get_task_id(): self.show_task_details(task_id),
                            style=ButtonStyle(
                                bgcolor=self.page.theme.color_scheme.primary,
                                color={"": colors.WHITE},
                                shape=RoundedRectangleBorder(radius=10),
                                padding=Padding(15, 10, 15, 10)
                            )
                        )
                    )
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
                ft.Text(f"{status.value} Tasks", size=20, weight=ft.FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                task_data_table
            ]))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Tasks of Project '{project.get_project_name()}'", size=30, weight=ft.FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    *task_controls,
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go(f"/project_management/{self.project_id}"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.on_primary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def group_tasks_by_status(self, tasks):
        tasks_by_status = {status: [] for status in Status}
        for task in tasks:
            status = task.get_status()
            tasks_by_status[status].append(task)
        return tasks_by_status

    def show_task_details(self, task_id):
        self.page.go(f"/show_task_details/{task_id}")
        self.page.update()
        logger.info(f"User '{self.db.get_current_user_username(self.page)}' viewed details of task ID '{task_id}'.")



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
            Text(f"Description: {task.get_description()}", size=20),
            Text(f"Priority: {task.get_priority().name}", size=20),
            Text(f"Status: {task.get_status().name}", size=20),
            Text(f"Start Date: {task.get_start_datetime()}", size=20),
            Text(f"End Date: {task.get_end_datetime()}", size=20),
            Text(f"Assignees: {', '.join([self.db.get_user_by_id(assignee_id).get_username() for assignee_id in task.get_assignees()])}", size=20),
            ElevatedButton(
                text="Show Comments",
                on_click=lambda e: self.show_comments(task_id),
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.on_primary_container,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            ),
            ElevatedButton(
                text="Show History",
                on_click=lambda e: self.show_history(task_id),
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.secondary,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            ),
        ]

        assignee_names = [self.db.get_user_by_id(task_assignee).get_username() for task_assignee in task.get_assignees()]
        if self.db.get_current_user(self.page).get_username() in assignee_names:
            task_details_controls.append(
                ElevatedButton(
                    text="Change Status",
                    on_click=lambda e: self.change_task_status(task_id),
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.secondary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )

        if self.db.get_current_user_id(self.page) == project.get_leader_id():
            task_details_controls.append(
                ElevatedButton(
                    text="Change Priority",
                    on_click=lambda e: self.change_task_priority(task_id),
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_surface,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )
            task_details_controls.append(
                ElevatedButton(
                    text="Add Assignees",
                    on_click=lambda e: self.add_assignees(task_id),
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )
            task_details_controls.append(
                ElevatedButton(
                    text="Remove Assignees",
                    on_click=lambda e: self.remove_assignees(task_id),
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )

        task_details_controls.append(
            ElevatedButton(
                text="Back",
                on_click=lambda e: self.cancel_dialog(),
                width=300,
                style=ButtonStyle(
                    bgcolor={"": colors.BLUE_ACCENT_700},
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            )
        )

        return Container(
            content=Column(
                controls=[
                    Text(f"Task: {task.get_title()} for Project: {project.get_project_name()}", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    *task_details_controls
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def add_assignees(self, task_id):
        self.page.go(f"/add_assignees/{task_id}")
        self.page.update()

    def remove_assignees(self, task_id):
        self.page.go(f"/remove_assignees/{task_id}")
        self.page.update()

    def change_task_status(self, task_id):
        self.page.go(f"/change_task_status/{task_id}")
        self.page.update()

    def change_task_priority(self, task_id):
        self.page.go(f"/change_task_priority/{task_id}")
        self.page.update()

    def show_comments(self, task_id):
        self.page.go(f"/show_comments/{task_id}")
        self.page.update()
        logger.info(f"User '{self.db.get_current_user_username(self.page)}' viewed comments for task ID '{task_id}'.")

    def show_history(self, task_id):
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
        self.add_comment_field = ft.TextField(label="Add Comment:", color=self.page.theme.color_scheme.on_secondary)
        self.username = db.get_current_user_username(page)

    def build(self):
        return self._build_comment_view()

    def _build_comment_view(self):
        comments = self.db.get_task_comments(self.task_id)
        comment_boxes = self._build_comment_boxes(comments)

        self.comment_column = ft.Column(
            controls=[
                ft.Text("Comments", size=30, weight=ft.FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary),
                *comment_boxes,
                self.add_comment_field,
                ElevatedButton(
                    text="Add Comment",
                    on_click=self.add_comment,
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                ),
                ElevatedButton(
                    text="Back",
                    on_click=self.go_back,
                    width=300,
                    style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.primary,
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            ],
            alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=20
        )

        return ft.Container(
            content=self.comment_column,
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def _build_comment_boxes(self, comments):
        comment_boxes = []
        if not comments:
            comment_boxes.append(Text("No comments yet.", size=20))
        else:
            for comment in comments:
                author = comment.get_username()
                timestamp = comment.get_timestamp()
                content = comment.get_content()
                delete_button = None
                if author == self.username:
                    delete_button = ElevatedButton(
                        text="Delete",
                        on_click=lambda e, comment_content=content: self.delete_comment(e, comment_content),
                        width=100,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.secondary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(5, 5, 5, 5)
                        )
                    )

                comment_box = Container(
                    content=Column([
                        Text(f"{author} commented:", size=14, weight=ft.FontWeight.BOLD),
                        Text(content, size=16),
                        Text(f"at {timestamp}", size=12, italic=True, color=colors.GREY),
                        delete_button
                    ]),
                    padding=10,
                    border=border.all(1, color=colors.GREY),
                    border_radius=10,
                    margin=10,
                    bgcolor=self.page.theme.color_scheme.on_primary,
                    shadow=BoxShadow(blur_radius=5, spread_radius=1, color=colors.GREY, offset=Offset(2, 2))
                )
                
                comment_boxes.append(comment_box)

        return comment_boxes

    def add_comment(self, e):
        comment_content = self.add_comment_field.value
        if comment_content:
            username = self.username
            self.db.add_comment(self.task_id, username, comment_content)
            self.db.add_task_history(self.task_id, f"Added comment: '{comment_content}'", username)
            self.add_comment_field.value = ""
            self.refresh_comments()
            logger.info(f"User '{username}' added the comment '{comment_content}' to task ID '{self.task_id}'.")

    def delete_comment(self, e, comment_content):
        comment = self.db.get_comment(self.task_id, self.username, comment_content)
        if comment:
            self.db.delete_comment(self.task_id, self.username, comment_content)
            self.db.add_task_history(self.task_id, f"Deleted comment: '{comment_content}'", self.username)
            self.refresh_comments()
            logger.info(f"User '{self.username}' deleted the comment '{comment_content}' from task ID '{self.task_id}'.")

    def refresh_comments(self):
        comments = self.db.get_task_comments(self.task_id)
        comment_boxes = self._build_comment_boxes(comments)
        self.comment_column.controls = [
            ft.Text("Comments", size=30, weight=ft.FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary),
            *comment_boxes,
            self.add_comment_field,
            ElevatedButton(
                text="Add Comment",
                on_click=self.add_comment,
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.on_primary,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            ),
            ElevatedButton(
                text="Back",
                on_click=self.go_back,
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.primary,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            )
        ]
        self.comment_column.update()

    def go_back(self, e):
        show_task_details = ShowTaskDetailsWindow(self.db, self.task_id , self.page)
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
            options=[ft.dropdown.Option(priority.name) for priority in priority_options],
            value=current_priority,
            bgcolor=colors.WHITE,
            color=self.page.theme.color_scheme.surface_variant,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"Change Priority for Task '{task.get_title()}'", size=30, weight=ft.FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    self.priority_dropdown,
                    ElevatedButton(
                        text="Save",
                        on_click=self.save_priority,
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.primary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    ),
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor={"": colors.BLUE_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

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
            color=self.page.theme.color_scheme.surface_variant,
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
        logger.info(f"User '{username}' changed status of task '{task.get_title()}' from '{current_status}' to '{new_status}'.")
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
                        content=ft.Column([
                            ft.Text(f"{history.get_author()}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{history.get_action()}", size=16),
                            ft.Text(f"at: {history.get_timestamp()}", size=12, italic=True, color=colors.GREY),
                        ]),
                        padding=10,
                        border=ft.border.all(1, color=colors.GREY),
                        border_radius=10,
                        margin=10,
                        bgcolor=self.page.theme.color_scheme.on_primary,
                        shadow=ft.BoxShadow(blur_radius=5, spread_radius=1, color=colors.GREY, offset=ft.Offset(2, 2))
                    )
                )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(f"History of Task '{task.get_title()}'", size=30, weight=ft.FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    *history_controls,
                    ElevatedButton(
                        text="Back",
                        on_click=lambda e: self.page.go(f"/show_task_details/{self.task_id}"),
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.primary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )


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

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Add Assignees to Task", size=30, weight=ft.FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    ft.Column(self.member_checkboxes),
                    ElevatedButton(
                        text="Save",
                        on_click=self.save_assignees,
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.primary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    ),
                    ElevatedButton(
                        text="Cancel",
                        on_click=self.cancel_dialog,
                        width=300,
                        style=ButtonStyle(
                            bgcolor={"": colors.RED_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

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

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Remove Assignees from Task", size=30, weight=ft.FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary,),
                    ft.Column(self.member_checkboxes),
                    ElevatedButton(
                        text="Save",
                        on_click=self.remove_assignees,
                        width=300,
                        style=ButtonStyle(
                            bgcolor=self.page.theme.color_scheme.primary,
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    ),
                    ElevatedButton(
                        text="Cancel",
                        on_click=self.cancel_dialog,
                        width=300,
                        style=ButtonStyle(
                            bgcolor={"": colors.RED_ACCENT_700},
                            color={"": colors.WHITE},
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    )
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

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

        member_section = Column(
            controls=[
                Text("Project Members", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                Column(self.member_checkboxes)
            ]
        )

        if current_user_id == leader_id:
            member_section.controls.append(
                ElevatedButton(
                    text="Remove Selected Members",
                    on_click=self.remove_members,
                    width=300,
                    style=ButtonStyle(
                        bgcolor={"": colors.RED_ACCENT_700},
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )
            member_section.controls.append(
                ElevatedButton(
                    text="Add Members",
                    on_click=self.show_non_members,
                    width=300,
                    style=ButtonStyle(
                        bgcolor={"": colors.PURPLE_ACCENT_700},
                        color={"": colors.WHITE},
                        shape=RoundedRectangleBorder(radius=10),
                        padding=Padding(15, 10, 15, 10)
                    )
                )
            )

        member_section.controls.append(
            ElevatedButton(
                text="Back",
                on_click=self.cancel_dialog,
                width=300,
                style=ButtonStyle(
                    bgcolor=self.page.theme.color_scheme.on_primary,
                    color={"": colors.WHITE},
                    shape=RoundedRectangleBorder(radius=10),
                    padding=Padding(15, 10, 15, 10)
                )
            )
        )

        return Container(
            content=Column(
                controls=[
                    member_section
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def show_non_members(self, e):
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
                    Container(
                        content=Column(
                            controls=[
                                Text("Add Members", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                                Column(self.non_member_checkboxes, alignment=MainAxisAlignment.START, spacing=10),
                                ElevatedButton(
                                    text="Add Selected Members",
                                    on_click=self.add_members,
                                    width=300,
                                    style=ButtonStyle(
                                        bgcolor={"": colors.GREEN_ACCENT_700},
                                        color={"": colors.WHITE},
                                        shape=RoundedRectangleBorder(radius=10),
                                        padding=Padding(15, 10, 15, 10)
                                    )
                                ),
                                ElevatedButton(
                                    text="Cancel",
                                    on_click=self.cancel_add_members,
                                    width=300,
                                    style=ButtonStyle(
                                        bgcolor={"": colors.RED_ACCENT_700},
                                        color={"": colors.WHITE},
                                        shape=RoundedRectangleBorder(radius=10),
                                        padding=Padding(15, 10, 15, 10)
                                    )
                                )
                            ],
                            alignment=MainAxisAlignment.CENTER,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                            spacing=20
                        ),
                        bgcolor=self.page.theme.color_scheme.background,
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS,
                bgcolor=self.page.theme.color_scheme.background,
            )
        )
        self.page.update()

    def add_members(self, e):
        selected_user_ids = [cb.key for cb in self.non_member_checkboxes if cb.value]
        if len(selected_user_ids) > 0:
            for user_id in selected_user_ids:
                self.db.add_project_member(self.project_id, user_id)
                logger.info(f"User '{self.db.get_user_by_id(user_id).get_username()}' added to project '{self.project_id}' by user '{self.db.get_current_user_username(self.page)}'.")

            self.update_member_checkboxes()
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Members added successfully!"))
            self.page.snack_bar.open = True
            self.page.go(f"/project_members/{self.project_id}")
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select a member first!"))
            self.page.snack_bar.open = True
            self.page.update()

    def remove_members(self, e):
        selected_member_ids = [cb.key for cb in self.member_checkboxes if cb.value]
        if len(selected_member_ids) > 0:
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
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select a member first!"))
            self.page.snack_bar.open = True
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
        self.start_date_picker = None
        self.end_date_picker = None
        self.start_date_value = None
        self.end_date_value = None

    def build(self):
        self.error_message = Text(value="", color=colors.RED)
        self.title_field = TextField(label="Title", width=400, color=self.page.theme.color_scheme.on_secondary)
        self.description_field = TextField(label="Description", width=400, color=self.page.theme.color_scheme.on_secondary)
        self.priority_dropdown = Dropdown(
            label="Priority",
            options=[
                ft.dropdown.Option("CRITICAL"),
                ft.dropdown.Option("HIGH"),
                ft.dropdown.Option("MEDIUM"),
                ft.dropdown.Option("LOW")
            ],
            value="LOW",
            width=400,
            bgcolor=self.page.theme.color_scheme.background,
            color=self.page.theme.color_scheme.on_secondary
        )

        def start_date_change(e):
            self.start_date_value = self.start_date_picker.value

        def end_date_change(e):
            self.end_date_value = self.end_date_picker.value

        self.start_date_picker = DatePicker(
            on_change=start_date_change,
            first_date=date(2023, 1, 1),
            last_date=date(2025, 12, 31)
        )

        self.end_date_picker = DatePicker(
            on_change=end_date_change,
            first_date=date(2023, 1, 1),
            last_date=date(2025, 12, 31)
        )

        self.page.overlay.append(self.start_date_picker)
        self.page.overlay.append(self.end_date_picker)

        start_date_button = ElevatedButton(
            "Pick Start Date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.start_date_picker.pick_date(),
            width=400,
            bgcolor=self.page.theme.color_scheme.on_background,
        )

        end_date_button = ElevatedButton(
            "Pick End Date",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.end_date_picker.pick_date(),
            width=400,
            bgcolor=self.page.theme.color_scheme.on_background,
        )

        self.member_checkboxes = []
        self.choose_assignees_label = Text("Choose Assignees:", size=20, weight=FontWeight.BOLD, color=self.page.theme.color_scheme.on_secondary)

        active_users = self.db.get_project_members(self.project_id)
        active_users.append(self.db.get_user_by_id(self.db.get_project(self.project_id).get_leader_id()))
        for user in active_users:
            cb = Checkbox(label=user.get_username(), key=user.get_id())
            self.member_checkboxes.append(cb)

        return Container(
            content=Column(
                controls=[
                    Text("Add a New Task", size=30, weight=FontWeight.BOLD,  color=self.page.theme.color_scheme.on_secondary),
                    self.title_field,
                    self.description_field,
                    self.priority_dropdown,
                    start_date_button,
                    end_date_button,
                    self.choose_assignees_label,
                    Column(self.member_checkboxes, alignment=MainAxisAlignment.START, spacing=10),
                    ElevatedButton(
                        text="Save",
                        on_click=self.save_task,
                        width=300,
                        style=ButtonStyle(
                        bgcolor=self.page.theme.color_scheme.on_background,
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                        )
                    ),
                    ElevatedButton(
                        text="Cancel",
                        on_click=self.cancel_dialog,
                        width=300,
                         style=ButtonStyle(
                         bgcolor=self.page.theme.color_scheme.on_background,
                            shape=RoundedRectangleBorder(radius=10),
                            padding=Padding(15, 10, 15, 10)
                         )
                    ),
                    self.error_message
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=20
            ),
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=self.page.theme.color_scheme.background,
            expand=True
        )

    def validate_fields(self):
        title = self.title_field.value
        description = self.description_field.value
        start_date = self.start_date_value
        end_date = self.end_date_value

        if not title:
            self.show_snackbar("Title field cannot be empty.")
            return False
        if not description:
            self.show_snackbar("Description field cannot be empty.")
            return False
        if not start_date:
            self.start_date_value =  datetime.now()
        if not end_date:
            self.end_date_value = (datetime.now() + timedelta(hours=24))
        if start_date and end_date and end_date < start_date:
            self.show_snackbar("End date cannot be less than start date")
            return False

        return True

    def save_task(self, e):
        if not self.validate_fields():
            return

        start_date = self.start_date_value
        end_date = self.end_date_value

        selected_assignees = [cb.key for cb in self.member_checkboxes if cb.value]

        new_task = Task(
            project_id=self.project_id,
            title=self.title_field.value,
            description=self.description_field.value,
            priority=self.priority_dropdown.value,
            status="BACKLOG",
            assignees=selected_assignees,
            start_datetime=start_date,
            end_datetime=end_date
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

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar = snackbar
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    db = Database()


#light theme
    light_theme = ft.Theme(
        font_family="Roboto",
        color_scheme=ft.ColorScheme(
            primary=ft.colors.TEAL_ACCENT_700,
            background=ft.colors.TEAL_50,
            on_primary=ft.colors.TEAL_800,
            primary_container=ft.colors.PINK,
            on_primary_container=ft.colors.PINK_300,
            secondary=ft.colors.PINK,
            on_background=ft.colors.BLACK,
            on_secondary=ft.colors.BLACK,
            on_surface=ft.colors.TEAL_100,
            surface_variant= ft.colors.TEAL_200,
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
        font_family="Roboto",
        color_scheme=ft.ColorScheme(
            primary=ft.colors.PURPLE,
            background=ft.colors.BLACK,
            on_primary=ft.colors.DEEP_PURPLE,
            primary_container=ft.colors.INDIGO,
            on_primary_container=ft.colors.DEEP_PURPLE_ACCENT_700,
            secondary=ft.colors.PURPLE,
            on_background=ft.colors.WHITE,
            on_secondary=ft.colors.WHITE,
            on_surface=ft.colors.DEEP_PURPLE_100,
            surface_variant= ft.colors.PURPLE_300,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=ft.colors.WHITE),
            headline_large=ft.TextStyle(color=ft.colors.WHITE),
            title_medium=ft.TextStyle(color=ft.colors.WHITE),
            body_large=ft.TextStyle(color=ft.colors.BLACK),
            body_small=ft.TextStyle(color=ft.colors.BLACK),
            display_large=ft.TextStyle(color=ft.colors.WHITE),
            display_medium=ft.TextStyle(color=ft.colors.WHITE),
            display_small=ft.TextStyle(color=ft.colors.WHITE),
            headline_medium=ft.TextStyle(color=ft.colors.WHITE),
            headline_small=ft.TextStyle(color=ft.colors.WHITE),
            label_large=ft.TextStyle(color=ft.colors.WHITE),
            label_medium=ft.TextStyle(color=ft.colors.BLACK),
            label_small=ft.TextStyle(color=ft.colors.WHITE),
            title_large=ft.TextStyle(color=ft.colors.WHITE),
            title_small=ft.TextStyle(color=ft.colors.WHITE)
        )
    )

 
    page.theme = light_theme
    page.update()

    def switch_theme(e):
        if page.theme == light_theme:
            page.theme = dark_theme
        else:
            page.theme = light_theme
        page.update()
        update_views_theme()  

    def update_views_theme():
        
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
                alignment=ft.alignment.center,
                padding=20,
            )

        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        create_common_container(
                            Column(
                                controls=[
                                    Text("Welcome!", size=40, weight=FontWeight.BOLD, color=ft.colors.PINK_ACCENT_700),
                                    ElevatedButton(
                                        text="Login",
                                        on_click=lambda e: page.go("/login"),
                                        width=300,
                                        style=ButtonStyle(
                                            shape=RoundedRectangleBorder(radius=10),
                                            padding=Padding(15, 10, 15, 10)
                                        )
                                    ),
                                    ElevatedButton(
                                        text="Sign Up",
                                        on_click=lambda e: page.go("/signup"),
                                        width=300,
                                         style=ButtonStyle(
                                             shape=RoundedRectangleBorder(radius=10),
                                             padding=Padding(15, 10, 15, 10)
                                         )
                                    ),
                                    ElevatedButton(
                                        text="Switch Theme",
                                        on_click=switch_theme,
                                        width=300,
                                        style=ButtonStyle(
                                            bgcolor={"": colors.PINK_ACCENT_700},
                                            color={"": colors.WHITE},
                                            shape=RoundedRectangleBorder(radius=10),
                                            padding=Padding(15, 10, 15, 10)
                                        )
                                    ),
                                    ElevatedButton(
                                        text="Exit",
                                        on_click=lambda e: page.window_destroy(),
                                        width=300,
                                         style=ButtonStyle(
                                             shape=RoundedRectangleBorder(radius=10),
                                             padding=Padding(15, 10, 15, 10)
                                         )
                                    ),
                                ],
                                alignment=MainAxisAlignment.CENTER,
                                horizontal_alignment=CrossAxisAlignment.CENTER,
                                spacing=20
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
                            bgcolor=page.theme.color_scheme.background,
                            expand=True
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
                            bgcolor=page.theme.color_scheme.background,
                            expand=True
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
                            bgcolor=page.theme.color_scheme.background,
                        ),
                    ],
                    scroll=ft.ScrollMode.ALWAYS,
                    bgcolor=page.theme.color_scheme.background,

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
