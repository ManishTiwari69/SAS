import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from db_config import get_db_connection
from datetime import date
import sys
import os
from db_config import check_db_status 
from edit_admin import edit_admin
import update_student
from student_register import register_student
import check_camera
import admin_register
import recognize
import view_attendance
from session import user_session

class AdminDashboard:
    def __init__(self, root, admin_id):
        # --- THE GATEKEEPER ---
        if not user_session.is_logged_in:
            self.redirect_to_login(root)
            return

        self.root = root
        self.admin_id = admin_id
        self.admin_name = self.get_admin_name()
        
        self.root.title("Attenad - AI Attendance System")
        self.root.geometry("1300x850")
        self.root.configure(bg="#f8f9fa")

        # UI Colors
        self.SIDEBAR_COLOR = "#1a1c23"
        self.PRIMARY_COLOR = "#00d084" 

        self.setup_layout()

    def redirect_to_login(self, root):
        """Force redirect back to login screen with a message"""
        user_session.login_message = "⚠️Please Login "
        for widget in root.winfo_children():
            widget.destroy()
        import login
        login.LoginApp(root)

    def get_admin_name(self):
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT first_name FROM admin_details WHERE admin_id = %s", (self.admin_id,))
            result = cursor.fetchone()
            db.close()
            return result[0] if result else "Admin"
        except Exception:
            return "Admin"

    # --- THE MISSING METHOD ---
    def get_attendance_stats(self):
        try:
            db = get_db_connection()
            cursor = db.cursor()
            today = date.today()
            
            cursor.execute("SELECT COUNT(*) FROM students")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT student_id) FROM attendance_logs WHERE log_date = %s", (today,))
            present = cursor.fetchone()[0]
            
            db.close()
            return {"total": total, "present": present, "absent": total - present}
        except Exception as e:
            print(f"Database Error: {e}")
            return {"total": 0, "present": 0, "absent": 0}

    def setup_layout(self):
        # 1. --- SIDEBAR (Left) ---
        self.sidebar = tk.Frame(self.root, bg=self.SIDEBAR_COLOR, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="🅰 Attenad", font=("Arial", 20, "bold"), 
                 bg=self.SIDEBAR_COLOR, fg=self.PRIMARY_COLOR).pack(pady=40)

        # Sidebar Buttons
        self.add_menu_item("🏠 Dashboard Overview", self.render_overview)
        self.add_menu_item("📷 Check Camera", lambda: check_camera.camer(self.content_area, self.render_overview))
        self.add_menu_item("🔐 Register ADMIN", lambda: admin_register.register_admin(self.content_area))
        self.add_menu_item("⚙️ Edit Profile", lambda: edit_admin(self.content_area, self.admin_id, self.render_overview))
        self.add_menu_item("👨‍🎓 Register Student", lambda: register_student(self.content_area, self.render_overview))
        self.add_menu_item("✏️ Update Student", lambda: update_student.update_student(self.content_area))
        self.add_menu_item("🛡️ Recognize", lambda: recognize.recognize_attendance(self.root, self.render_overview))
        self.add_menu_item("📊 Records", lambda: view_attendance.show_attendance(self.content_area))
        self.add_menu_item("🚪 Logout", self.handle_logout)

        # 2. --- TOPBAR (Top) ---
        self.topbar = tk.Frame(self.root, bg="white", height=70, bd=1, relief="flat")
        self.topbar.pack(side="top", fill="x")
        
        tk.Label(self.topbar, text=f"Welcome, {self.admin_name} 👋", font=("Arial", 12, "bold"), 
                 bg="white", fg="#333").pack(side="right", padx=40, pady=20)

        # 3. --- CONTENT AREA (Center) ---
        self.content_area = tk.Frame(self.root, bg="#f8f9fa")
        self.content_area.pack(side="right", fill="both", expand=True)

        self.render_overview()

    def handle_logout(self):
        user_session.is_logged_in = False
        user_session.current_user = None
        self.redirect_to_login(self.root)

    def add_menu_item(self, text, command):
        def wrapper():
    # Check if the content_area actually exists in the Tcl/Tk interpreter
            if self.content_area.winfo_exists():
                for widget in self.content_area.winfo_children():
                    widget.destroy()
                command()

        btn = tk.Button(self.sidebar, text=f"  {text}", font=("Arial", 11), bg=self.SIDEBAR_COLOR, 
                        fg="white", bd=0, activebackground="#2d2f39", activeforeground=self.PRIMARY_COLOR,
                        anchor="w", padx=25, pady=12, cursor="hand2", command=wrapper)
        btn.pack(fill="x", pady=2)

    def render_overview(self):
        for w in self.content_area.winfo_children(): w.destroy()
        stats = self.get_attendance_stats()
        
        card_frame = tk.Frame(self.content_area, bg="#f8f9fa")
        card_frame.pack(fill="x", padx=40, pady=30)

        self.create_stat_card(card_frame, "TOTAL STUDENTS", stats['total'], "#ffffff", 0)
        self.create_stat_card(card_frame, "PRESENT TODAY", stats['present'], self.PRIMARY_COLOR, 1)
        self.create_stat_card(card_frame, "ABSENT TODAY", stats['absent'], "#ffffff", 2)

    def create_stat_card(self, parent, title, value, color, col):
        fg_color = "white" if color == self.PRIMARY_COLOR else "#333"
        card = tk.Frame(parent, bg=color, width=280, height=130, highlightthickness=1, highlightbackground="#eee")
        card.grid(row=0, column=col, padx=15)
        card.grid_propagate(False)
        
        tk.Label(card, text=title, font=("Arial", 10, "bold"), 
                 bg=color, fg="#777" if color=="#ffffff" else "white").pack(pady=(25,5))
        tk.Label(card, text=str(value), font=("Arial", 28, "bold"), bg=color, fg=fg_color).pack()



if __name__ == "__main__":
   
    
    if not check_db_status():
        temp_root = tk.Tk()
        temp_root.withdraw() 
        messagebox.showerror("Database Connection Error", 
                             "Could not connect to MySQL server.\n"
                             "Please ensure XAMPP/MySQL is running and try again.")
        temp_root.destroy()
        sys.exit()

    root = tk.Tk()
    # In a real scenario, this admin_id would come from your login logic
    # For now, we pass 1 to test the dashboard
    app = AdminDashboard(root, admin_id=1) 
    root.mainloop()