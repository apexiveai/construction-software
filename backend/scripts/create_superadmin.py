
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main():
    db = SessionLocal()

    try:
        existing = db.scalar(
            select(User).where(User.is_superuser.is_(True))
        )

        if existing:
            print("A Super Admin account already exists.")
            return

        email = input("Super Admin Email: ").strip().lower()
        full_name = input("Full Name: ").strip()
        password = getpass("Password: ")
        confirm_password = getpass("Confirm Password: ")

        if not email or not full_name:
            print("Email and full name are required.")
            return

        if password != confirm_password:
            print("Passwords do not match.")
            return

        if len(password) < 12:
            print("Password must contain at least 12 characters.")
            return

        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print("This email is already registered.")
            return

        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            is_active=True,
            is_superuser=True,
        )

        db.add(user)
        db.commit()

        print("=" * 50)
        print("SUPER ADMIN CREATED SUCCESSFULLY")
        print("Email:", email)
        print("User ID:", user.id)
        print("=" * 50)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
