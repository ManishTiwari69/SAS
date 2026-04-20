import mysql.connector
from mysql.connector import pooling
import mysql.connector.errors

# Create a connection pool (keeps connections ready in the background)
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="sas_pool",
    pool_size=32,  # Allows up to 5 simultaneous database actions
    host="localhost",
    user="root",
    password="",
    database="attendance_db"
)

def get_db_connection():
    """Pulls a connection from the pre-warmed pool."""
    return db_pool.get_connection()

def check_db_status():
    """Pings the server to ensure it's alive."""
    try:
        db = get_db_connection()
        if db.is_connected():
            db.close() # Returns connection to the pool
            return True
    except Exception as e:
        print(f"❌ Database Offline: {e}")
        return False
    return False