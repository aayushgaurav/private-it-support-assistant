
from getpass import getpass

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.database.models import User
from app.core.security import hash_password


def create_admin():
    print("=== Admin Account Creation ===")

    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip().lower()

    if len(username) < 3 or len(username) > 50:
        print("Username must contain 3–50 characters.")
        return

    if "@" not in email or "." not in email:
        print("Enter a valid email address.")
        return

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if len(password) < 12 or len(password) > 128:
        print("Password must contain 12–128 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(
                (User.username == username)
                | (User.email == email)
            )
        )

        if existing_user:
            print("Username or email already exists.")
            return

        admin = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("Administrator account created successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
