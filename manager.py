import argparse
import sqlite3
import hashlib
from database import Database
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="User Management System")
    parser.add_argument("action", choices=["create-admin", "purge-data"], help="Action to perform")
    parser.add_argument("--username", help="Admin username")
    parser.add_argument("--password", help="Admin password")

    args = parser.parse_args()

    db = Database()

    if args.action == "create-admin":
        if not db.admin_exists():
            db.create_admin(args.username, args.password)
            logger.info("Admin created successfully")
            print("Admin created successfully!")
        else:
            logger.warning("Attempting to create admin while admin already exist")
            print("Admin already exists.")
    elif args.action == "purge-data":
        db.purge_data()
        logger.info("All data purged successfully")
        print("All data purged successfully.")

if __name__ == "__main__":
    main()





# def main():
#     parser = argparse.ArgumentParser(description="User Management System")
#     parser.add_argument("action", choices=["create-admin"], help="Action to perform")
#     parser.add_argument("--username", help="Admin username")
#     parser.add_argument("--password", help="Admin password")

#     args = parser.parse_args()

#     if args.action == "create-admin":
#         db = Database()
#         if not db.admin_exists():
#             db.create_admin(args.username, args.password)
#            # print("Admin user created successfully!")
#         else:
#             print("Admin user already exists.")

# if __name__ == "__main__":
#     main()


