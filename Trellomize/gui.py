# import tkinter as tk
# from tkinter import ttk, messagebox
# import tkinter.simpledialog  # Import simpledialog from tkinter module
# from project import Project

# class LoginWindow:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Login")
        
#         self.label_username = ttk.Label(root, text="Username:")
#         self.label_password = ttk.Label(root, text="Password:")
#         self.entry_username = ttk.Entry(root)
#         self.entry_password = ttk.Entry(root, show="*")
#         self.button_login = ttk.Button(root, text="Login", command=self.login)
        
#         self.label_username.grid(row=0, column=0, sticky="e", padx=5, pady=5)
#         self.entry_username.grid(row=0, column=1, padx=5, pady=5)
#         self.label_password.grid(row=1, column=0, sticky="e", padx=5, pady=5)
#         self.entry_password.grid(row=1, column=1, padx=5, pady=5)
#         self.button_login.grid(row=2, columnspan=2, pady=10)

#     def login(self):
#         # Hardcoded username and password for demonstration
#         username = self.entry_username.get()
#         password = self.entry_password.get()

#         if username == "admin" and password == "admin":
#             messagebox.showinfo("Success", "Login successful!")
#             self.root.destroy()  # Close login window
#             MainWindow(tk.Tk())  # Open main window
#         else:
#             messagebox.showerror("Error", "Invalid username or password!")

# class MainWindow:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Main Window")

#         self.label_main = ttk.Label(root, text="Welcome to the Main Window", font=("Arial", 18, "bold"))
#         self.label_main.pack(pady=20)

#         self.button_create_project = ttk.Button(root, text="Create Project", command=self.create_project)
#         self.button_create_project.pack()

#     def create_project(self):
#         project_name = tk.simpledialog.askstring("Create Project", "Enter project name:")
#         if project_name:
#             project = Project(project_name)
#             messagebox.showinfo("Success", f"Project '{project_name}' created successfully!")
#         else:
#             messagebox.showerror("Error", "Please enter a project name!")

# def main():
#     root = tk.Tk()
#     LoginWindow(root)
#     root.mainloop()

# if __name__ == "__main__":
#     main()
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import re
import os
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
    
    print(os.getcwd())

    def add_admin(self, username, password):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, isadmin) VALUES (?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, True))
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

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
    
    def get_all_users(self):
       query = "SELECT * FROM users WHERE username != ?"  # Exclude the admin user
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

class LoginWindow:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("Do you want to login or sign up?")
        self.button_login = ttk.Button(root, text="Login", command=self.show_login)
        self.button_signup = ttk.Button(root, text="Sign Up", command=self.show_signup)

        self.button_login.pack(pady=10)
        self.button_signup.pack(pady=10)

    def show_login(self):
        self.button_login.pack_forget()
        self.button_signup.pack_forget()
        self.root.title("Login")
        self.label_username = ttk.Label(self.root, text="Username:")
        self.label_password = ttk.Label(self.root, text="Password:")
        self.entry_username = ttk.Entry(self.root)
        self.entry_password = ttk.Entry(self.root, show="*")
        self.button_login_submit = ttk.Button(self.root, text="Login", command=self.login)

        self.label_username.pack()
        self.entry_username.pack()
        self.label_password.pack()
        self.entry_password.pack()
        self.button_login_submit.pack(pady=10)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if self.check_credentials(username, password):
            if self.check_active(username):
                messagebox.showinfo("Success", "Login successful!")
                self.root.destroy()
                MainWindow(tk.Tk(), username, self.db)  # Pass username to MainWindow
            else:
                messagebox.showerror("Error", "Your account is inactive. Please contact the administrator.")
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    def check_active(self, username):
        query = "SELECT active FROM users WHERE username=?"
        result = self.db.conn.execute(query, (username,)).fetchone()
        return result[0] if result else False

    def check_credentials(self, username, password):
        hashed_password = self.db._hash_password(password)
        query = "SELECT * FROM users WHERE username=? AND password=?"
        result = self.db.conn.execute(query, (username, hashed_password)).fetchone()
        return result is not None

    def show_signup(self):
        self.button_login.pack_forget()
        self.button_signup.pack_forget()
        self.root.title("Sign Up")
        self.label_username = ttk.Label(self.root, text="Username:")
        self.label_email = ttk.Label(self.root, text="Email:")
        self.label_password = ttk.Label(self.root, text="Password:")
        self.entry_username = ttk.Entry(self.root)
        self.entry_email = ttk.Entry(self.root)
        self.entry_password = ttk.Entry(self.root, show="*")
        self.button_signup_submit = ttk.Button(self.root, text="Sign Up", command=self.signup)

        self.label_username.pack()
        self.entry_username.pack()
        self.label_email.pack()
        self.entry_email.pack()
        self.label_password.pack()
        self.entry_password.pack()
        self.button_signup_submit.pack(pady=10)

    def signup(self):
        username = self.entry_username.get()
        email = self.entry_email.get()
        password = self.entry_password.get()

        # Check if username already exists
        if self.username_exists(username):
            messagebox.showerror("Error", "Username already taken!")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long!")
            return

        # Check for other input validations
        if not username or not email or not self.check_email(email) or not password:
            messagebox.showerror("Error", "Invalid input!")
            return

        # Add user to the database
        self.db.add_user(username, password, email)
        messagebox.showinfo("Success", "Account created successfully!")
        self.root.destroy()
        MainWindow(tk.Tk())
        self.root.destroy()
        MainWindow(tk.Tk(), username, self.db)

    def username_exists(self, username):
        query = "SELECT * FROM users WHERE username=?"
        result = self.db.conn.execute(query, (username,)).fetchone()
        return result is not None
    
    def check_email(self, email):
        return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))
    

   


class MainWindow:
    def __init__(self, root, username, db):
        self.root = root
        self.root.title("Main Window")
        self.username = username
        self.db = db

        self.label_main = ttk.Label(root, text="Welcome to the Main Window", font=("Arial", 18, "bold"))
        self.label_main.pack(pady=20)

        self.button_create_project = ttk.Button(root, text="Create Project", command=self.create_project)
        self.button_create_project.pack()

        self.button_show_projects = ttk.Button(root, text="Show Projects", command=self.show_projects)
        self.button_show_projects.pack()

        if self.db.is_admin(self.username):
            self.button_manage_users = ttk.Button(root, text="Manage Users", command=self.manage_users)
            self.button_manage_users.pack()

    def create_project(self):
        project_name = tk.simpledialog.askstring("Create Project", "Enter project name:")
        if project_name:
            project = Project(project_name)
            messagebox.showinfo("Success", f"Project '{project_name}' created successfully!")
        else:
            messagebox.showerror("Error", "Please enter a project name!")



    def show_projects(self):
        # Logic to show projects
        pass

    def manage_users(self):
        # Open new window to manage users
        ManageUsersWindow(tk.Toplevel(), self.db)

class ManageUsersWindow:
    def __init__(self, root, db):
        self.root = root
        self.root.title("Manage Users")
        self.db = db

        self.label_title = ttk.Label(root, text="User Management", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        self.button_active_users = ttk.Button(root, text="Active Users", command=self.show_active_users)
        self.button_active_users.pack()

        self.button_inactive_users = ttk.Button(root, text="Inactive Users", command=self.show_inactive_users)
        self.button_inactive_users.pack()

        self.button_back = ttk.Button(root, text="Back", command=self.close_window)
        self.button_back.pack()

    def show_active_users(self):
        self.root.destroy()  # Close the current window
        ActiveUsersWindow(tk.Toplevel(), self.db)

    def show_inactive_users(self):
        self.root.destroy()  # Close the current window
        InactiveUsersWindow(tk.Toplevel(), self.db)

    def close_window(self):
        self.root.destroy()

class ActiveUsersWindow:
    def __init__(self, root, db):
        self.root = root
        self.root.title("Active Users")
        self.db = db

        self.label_title = ttk.Label(root, text="Active Users", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        self.button_back = ttk.Button(root, text="Back", command=self.close_window)
        self.button_back.pack()

        self.show_users()

    def show_users(self):
        users = self.db.get_all_active_users()
        if not users:
            ttk.Label(self.root, text="No active users found").pack()
        else:
            for user in users:
                frame = ttk.Frame(self.root)
                frame.pack(pady=5)
                ttk.Label(frame, text=user[1]).pack(side=tk.LEFT)  # Display username

                # Add inactive button
                ttk.Button(frame, text="Inactive", command=lambda u=user: self.inactivate_user(u[0])).pack(side=tk.LEFT)

    def inactivate_user(self, user_id):
        # Update user's active status to False
        self.db.inactivate_user(user_id)
        messagebox.showinfo("Success", "User inactivated successfully!")
        # Refresh the user list after inactivation
        self.root.destroy()
        ActiveUsersWindow(tk.Toplevel(), self.db)

    def close_window(self):
        self.root.destroy()


class InactiveUsersWindow:
    def __init__(self, root, db):
        self.root = root
        self.root.title("Inactive Users")
        self.db = db

        self.label_title = ttk.Label(root, text="Inactive Users", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        self.button_back = ttk.Button(root, text="Back", command=self.close_window)
        self.button_back.pack()

        self.show_users()

    

    def show_users(self):
       users = self.db.get_all_inactive_users()
       if not users:
           ttk.Label(self.root, text="No inactive users found").pack()
       else:
             for user in users:
                user_id, username, email, is_active = user  # Unpack the values correctly
                frame = ttk.Frame(self.root)
                frame.pack(pady=5)
                ttk.Label(frame, text=username).pack(side=tk.LEFT)  # Display username

            # Add active button
                ttk.Button(frame, text="Activate", command=lambda u=user: self.activate_user(u[0])).pack(side=tk.LEFT)

    def activate_user(self, user_id):
        # Update user's active status to True
        self.db.activate_user(user_id)
        messagebox.showinfo("Success", "User activated successfully!")
        # Refresh the user list after activation
        self.root.destroy()
        InactiveUsersWindow(tk.Toplevel(), self.db)

    def close_window(self):
        self.root.destroy()

def main():
    db = Database()
    root = tk.Tk()
    LoginWindow(root, db)
    root.mainloop()

if __name__ == "__main__":
    main()

