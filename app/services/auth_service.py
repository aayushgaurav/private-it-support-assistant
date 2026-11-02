from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User
from app.api.schemas import UserRegister
from app.core.security import hash_password, verify_password, create_access_token

def register_user(db: Session, user_data: UserRegister):
    username = user_data.username.strip()
    email = str(user_data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(
            (User.username == username) |
            (User.email == email)
        )
    )

    if existing_user:
        raise ValueError("Username or email already registered.")

    hashed_password = hash_password(user_data.password)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role="employee",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user(db: Session, username: str, password: str):
    user = db.scalar(
        select(User).where(User.username == username.strip())
    )

    if not user or not user.is_active:
        raise ValueError("Incorrect username or password.")

    if not verify_password(password, user.hashed_password):
        raise ValueError("Incorrect username or password.")

    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }