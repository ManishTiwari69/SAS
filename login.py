import tkinter as tk
from tkinter import messagebox
from db_config import get_db_connection

def validate_login(username, password, window):
    # For a student project, you can hardcode admin credentials or check DB
    # Let's check a 'users' table in MySQL for better marks!
    try:
        db = get_db_connection()
        cursor = db.cursor()
        query = "SELECT * FROM admins WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        db.close()

        if result:
            window.destroy() # Close login
            import main # Launch the dashboard
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password")
    except Exception as e:
        # Fallback for demo if DB table 'admins' doesn't exist yet
        if username == "admin" and password == "admin123":
            window.destroy()
            import main
        else:
            messagebox.showerror("Error", "Database connection failed or invalid credentials.")

def login_page():
    root = tk.Tk()
    root.title("Attendance System - Login")
    root.geometry("800x500")
    root.configure(bg="#2c3e50") # Matching your dashboard theme

    # Left Side: Card Template (Simulated)
    left_frame = tk.Frame(root, bg="#3498db", width=400, height=500)
    left_frame.pack(side="left", fill="both", expand=True)

    card_label = tk.Label(left_frame, text="🛡️\nSecure Access", fg="white", bg="#3498db", font=("Arial", 30, "bold"))
    card_label.place(relx=0.5, rely=0.4, anchor="center")
    
    sub_text = tk.Label(left_frame, text="Face Recognition Attendance\nManagement System", fg="white", bg="#3498db", font=("Arial", 12))
    sub_text.place(relx=0.5, rely=0.6, anchor="center")

    # Right Side: Login Form
    right_frame = tk.Frame(root, bg="white", width=400, height=500)
    right_frame.pack(side="right", fill="both", expand=True)

    tk.Label(right_frame, text="Login to System", font=("Arial", 20, "bold"), bg="white", fg="#2c3e50").pack(pady=(80, 20))

    # Username
    tk.Label(right_frame, text="Username", bg="white", fg="gray").pack(anchor="w", padx=50)
    user_entry = tk.Entry(right_frame, font=("Arial", 12), bd=0, highlightthickness=1, highlightbackground="lightgray")
    user_entry.pack(fill="x", padx=50, pady=5)

    # Password
    tk.Label(right_frame, text="Password", bg="white", fg="gray").pack(anchor="w", padx=50, pady=(10, 0))
    pass_entry = tk.Entry(right_frame, font=("Arial", 12), show="*", bd=0, highlightthickness=1, highlightbackground="lightgray")
    pass_entry.pack(fill="x", padx=50, pady=5)

    # Sign In Button
    btn_signin = tk.Button(right_frame, text="Sign In", bg="#3498db", fg="white", font=("Arial", 12, "bold"), 
                           command=lambda: validate_login(user_entry.get(), pass_entry.get(), root))
    btn_signin.pack(fill="x", padx=50, pady=30)

    root.mainloop()

if __name__ == "__main__":
    login_page()