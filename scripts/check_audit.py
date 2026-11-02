import sqlite3
from pathlib import Path

db_path = Path("data/users.db")

print("Database:", db_path.resolve())
print("Exists:", db_path.exists())

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

cursor.execute("""
    SELECT id, user_id, action, document_id, details, created_at
    FROM audit_logs
    ORDER BY id DESC
""")

print("\nAudit log details:")

for record in cursor.fetchall():
    print(record)

print("Tables:", cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM audit_logs")

print("Audit records:", cursor.fetchone()[0])

connection.close()