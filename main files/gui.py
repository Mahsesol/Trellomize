import npyscreen
import sqlite3
import hashlib
import re
from project import Project

DB_FILE = "users.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            isadmin BOOLEAN DEFAULT FALSE
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def add_user(self, username, password, email):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email) VALUES (?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, email))
        self.conn.commit()

    def add_admin(self, username, password):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, isadmin) VALUES (?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, True))
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def is_admin(self, username):
        query = "SELECT isadmin FROM users WHERE username=?"
        result = self.conn.execute(query, (username,)).fetchone()
        return result[0] == 1 if result else False

    def get_all_users(self):
        query = "SELECT * FROM users WHERE username != ?"
        return self.conn.execute(query, ("admin",)).fetchall()

    def get_all_active_users(self):
        query = "SELECT * FROM users WHERE active = 1"
        return self.conn.execute(query).fetchall()

    def inactivate_user(self, user_id):
        query = "UPDATE users SET active = 0 WHERE id = ?"
        self.conn.execute(query, (user_id,))
        self.conn.commit()

    def get_all_inactive_users(self):
        query = "SELECT * FROM users WHERE active = FALSE"
        return self.conn.execute(query).fetchall()

    def activate_user(self, user_id):
        query = "UPDATE users SET active = TRUE WHERE id = ?"
        self.conn.execute(query, (user_id,))
        self.conn.commit()


class MenuWindow(npyscreen.Form):
    def create(self):
        self.add(npyscreen.TitleText, name="Welcome to Project Management System!", editable=False)
        self.add(npyscreen.ButtonPress, name="Login", when_pressed_function=self.login)
        self.add(npyscreen.ButtonPress, name="Sign Up", when_pressed_function=self.signup)
        self.add(npyscreen.ButtonPress, name="Exit", when_pressed_function=self.exit_app)

    def login(self):
        self.parentApp.switchForm("LOGIN")

    def signup(self):
        self.parentApp.switchForm("SIGNUP")

    def exit_app(self):
        self.parentApp.setNextForm(None)
        self.parentApp.switchFormNow()


class LoginBox(npyscreen.ActionForm):
    def create(self):
        self.add(npyscreen.TitleText, name="Username:")
        self.add(npyscreen.TitlePassword, name="Password:")

    def on_ok(self):
        username = self.get_widget("Username:").value
        password = self.get_widget("Password:").value

        if self.check_credentials(username, password):
            if self.check_active(username):
                npyscreen.notify_confirm("Login successful!", title="Success")
                self.parentApp.setNextForm("PROJECT_BOARD")
                self.parentApp.username = username
            else:
                npyscreen.notify_confirm("Your account is inactive. Please contact the administrator.", title="Error")
        else:
            npyscreen.notify_confirm("Invalid username or password!", title="Error")

    def check_active(self, username):
        query = "SELECT active FROM users WHERE username=?"
        result = self.parentApp.db.conn.execute(query, (username,)).fetchone()
        return result[0] if result else False

    def check_credentials(self, username, password):
        hashed_password = self.parentApp.db._hash_password(password)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        result = self.parentApp.db.conn.execute(query, (username, hashed_password)).fetchone()
        return result is not None


class SaveBox(npyscreen.ActionPopup):
    def create(self):
        self.result = None
        self.add(npyscreen.FixedText, value="Changes Saved!", editable=False)
        self.add(npyscreen.ButtonPress, name="OK", when_pressed_function=self.close_popup)

    def close_popup(self):
        self.parentApp.switchFormPrevious()


class ProjectBoard(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = npyscreen.BoxTitle
    MAIN_WIDGET_CLASS_START_LINE = 2
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.projects = ["Project 1", "Project 2", "Project 3"]  # Sample projects

    def beforeEditing(self):
        self.wMain.values = self.projects
        self.wMain.display()


class MyApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        self.db = Database()
        self.username = None
        self.addForm("MAIN", MenuWindow)
        self.addForm("LOGIN", LoginBox)
        self.addForm("SIGNUP", npyscreen.ActionFormMinimal)
        self.addForm("PROJECT_BOARD", ProjectBoard)
        self.addForm("SAVE_BOX", SaveBox)


if __name__ == "__main__":
    app = MyApplication()
    app.run()
