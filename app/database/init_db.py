from app.database.connection import Base, engine
from app.database.models import User, AuditLog


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    initialize_database()