import bcrypt
from db_config import get_db_connection

def migrate_to_hash():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # 1. Fetch all admins and their current plain text passwords
        cursor.execute("SELECT id, password FROM admins")
        admins = cursor.fetchall()

        print(f"Found {len(admins)} records to migrate...")

        for admin_id, plain_password in admins:
            # Check if it's already hashed (bcrypt hashes start with $2b$ or $2a$)
            if plain_password.startswith("$2b$") or plain_password.startswith("$2a$"):
                print(f"Skipping ID {admin_id}: Already hashed.")
                continue

            # 2. Generate Hash
            byte_pwd = plain_password.encode('utf-8')
            hashed_pw = bcrypt.hashpw(byte_pwd, bcrypt.gensalt())

            # 3. Update the database
            cursor.execute("UPDATE admins SET password = %s WHERE id = %s", 
                           (hashed_pw, admin_id))
            print(f"Successfully migrated ID {admin_id}")

        db.commit()
        db.close()
        print("--- Migration Complete ---")

    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_to_hash()