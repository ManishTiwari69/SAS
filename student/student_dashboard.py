import tkinter as tk
from tkinter import messagebox, ttk
from db_config import get_db_connection

class StudentDashboard:
    def __init__(self, root, student_id):
        self.root = root
        self.student_id = student_id
        
        # 1. Setup Window
        self.root.title("Student Dashboard - Attendance & Leave")
        self.root.geometry("1300x850")
        
        # 2. Header Section
        self.header = tk.Frame(self.root, bg="#2c3e50", height=100)
        self.header.pack(side="top", fill="x")
        
        tk.Label(self.header, text="STUDENT PORTAL", font=("Arial", 24, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=25)

        # 3. Main Content Area (Using two columns)
        self.main_container = tk.Frame(self.root, bg="#f4f7f6")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.setup_left_panel()  # Attendance View
        self.setup_right_panel() # Leave Application

    def setup_left_panel(self):
        """Displays Attendance Records in a Treeview"""
        left_panel = tk.LabelFrame(self.main_container, text=" My Attendance History ", 
                                   font=("Arial", 14, "bold"), bg="white", bd=2)
        left_panel.place(relx=0, rely=0, relwidth=0.58, relheight=1)

        # Treeview for Attendance
        columns = ("Date", "Status", "Time In")
        self.tree = ttk.Treeview(left_panel, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_attendance_data()

    def setup_right_panel(self):
        """Form to submit Leave Applications"""
        right_panel = tk.LabelFrame(self.main_container, text=" Apply for Leave ", 
                                    font=("Arial", 14, "bold"), bg="white", bd=2)
        right_panel.place(relx=0.6, rely=0, relwidth=0.4, relheight=1)

        tk.Label(right_panel, text="Reason for Leave:", bg="white").pack(anchor="w", padx=20, pady=(20, 5))
        self.leave_reason = tk.Entry(right_panel, font=("Arial", 12), bg="#e8f0fe")
        self.leave_reason.pack(fill="x", padx=20, pady=5)

        tk.Label(right_panel, text="Date (YYYY-MM-DD):", bg="white").pack(anchor="w", padx=20, pady=(10, 5))
        self.leave_date = tk.Entry(right_panel, font=("Arial", 12), bg="#e8f0fe")
        self.leave_date.pack(fill="x", padx=20, pady=5)

        tk.Button(right_panel, text="Submit Application", bg="#3498db", fg="white", 
                  font=("Arial", 12, "bold"), command=self.submit_leave).pack(pady=30, padx=20, fill="x")

    def load_attendance_data(self):
        """Fetch attendance from DB for specific student"""
        try:
            db = get_db_connection()
            cursor = db.cursor()
            # Assuming your table is called 'attendance' and has a 'student_id' column
            query = "SELECT date, status, time_in FROM attendance WHERE student_id = %s ORDER BY date DESC"
            cursor.execute(query, (self.student_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                self.tree.insert("", "end", values=row)
            db.close()
        except Exception as e:
            print(f"Error loading attendance: {e}")

    def submit_leave(self):
        reason = self.leave_reason.get()
        date = self.leave_date.get()

        if not reason or not date:
            messagebox.showwarning("Input Error", "Please fill in all leave details.")
            return

        try:
            db = get_db_connection()
            cursor = db.cursor()
            # Assuming a 'leave_applications' table exists
            query = "INSERT INTO leave_applications (student_id, reason, leave_date, status) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (self.student_id, reason, date, 'Pending'))
            db.commit()
            db.close()
            
            messagebox.showinfo("Success", "Leave application submitted for approval.")
            self.leave_reason.delete(0, tk.END)
            self.leave_date.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not submit leave: {e}")