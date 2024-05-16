import argparse
import sqlite3
import hashlib

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

    def create_admin(self, username, password):
        hashed_password = self._hash_password(password)
        query = "INSERT INTO users (username, password, email, isadmin) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (username, hashed_password, "admin@admin.com", True))
        self.conn.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def admin_exists(self):
        query = "SELECT * FROM users WHERE isadmin = 1"
        result = self.conn.execute(query).fetchone()
        return result is not None

def main():
    parser = argparse.ArgumentParser(description="User Management System")
    parser.add_argument("action", choices=["create-admin"], help="Action to perform")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--password", help="Admin password")

    args = parser.parse_args()

    if args.action == "create-admin":
        db = Database()
        if not db.admin_exists():
            db.create_admin(args.username, args.password)
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    main()


