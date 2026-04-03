import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",      # Default XAMPP user
        password="",      # Default XAMPP password is empty
        database="attendance_db"
    )