"""
Database migration script: Hash all existing plaintext employee passwords using bcrypt.
"""
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from core.config import local_session, engine
from core.security import hash_password, verify_password
from models.employees import Employee

def migrate_passwords():
    print("Starting password migration to bcrypt...")
    
    # 1. Expand column length if needed
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE employees ALTER COLUMN password TYPE VARCHAR(255);"))
            conn.commit()
            print("Successfully ensured employees.password is VARCHAR(255).")
        except Exception as e:
            print(f"Column check note: {e}")

    # 2. Migrate existing plaintext passwords
    db = local_session()
    try:
        employees = db.query(Employee).order_by(Employee.employee_id.asc()).all()
        migrated_count = 0
        already_hashed_count = 0

        for emp in employees:
            current_pwd = emp.password or ""
            if current_pwd.startswith(("$2a$", "$2b$", "$2y$")):
                already_hashed_count += 1
                print(f"Employee #{emp.employee_id} ({emp.email}): Already hashed")
            else:
                plaintext = current_pwd if current_pwd else "password123"
                hashed = hash_password(plaintext)
                emp.password = hashed
                migrated_count += 1
                print(f"Employee #{emp.employee_id} ({emp.email}): Plaintext '{plaintext}' -> Hashed with bcrypt: {hashed[:15]}...")

        db.commit()
        print(f"\nMigration completed successfully!")
        print(f"Total employees: {len(employees)}")
        print(f"Migrated: {migrated_count}")
        print(f"Already hashed: {already_hashed_count}")

    except Exception as e:
        db.rollback()
        print(f"Error during password migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_passwords()

