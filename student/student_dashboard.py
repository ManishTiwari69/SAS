import tkinter as tk
from db_config import get_db_connection

import student_attendance
import student_leave_apply
import student_leave_history
import student_edit_profile


class StudentDashboard:
    def __init__(self, root, student_id):
        self.root = root
        self.student_id = student_id

        # Colors
        self.SIDEBAR_COLOR = "#1a1c23"
        self.PRIMARY_COLOR = "#00d084"
        self.BG_COLOR      = "#f8f9fa"

        self.root.title("Student Dashboard")
        self.root.geometry("1300x850")
        self.root.configure(bg=self.BG_COLOR)

        self._build_header()
        self._build_layout()

        # Default view on open
        self.show_attendance()

    # ------------------------------------------------------------------ #
    #  HEADER                                                              #
    # ------------------------------------------------------------------ #
    def _build_header(self):
        student_name = self._get_student_name()

        header = tk.Frame(self.root, bg=self.SIDEBAR_COLOR, height=70)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🎓  STUDENT PORTAL",
                 font=("Arial", 18, "bold"),
                 bg=self.SIDEBAR_COLOR, fg=self.PRIMARY_COLOR
                 ).pack(side="left", padx=30, pady=15)

        tk.Label(header, text=f"Welcome, {student_name} 👋",
                 font=("Arial", 12),
                 bg=self.SIDEBAR_COLOR, fg="white"
                 ).pack(side="right", padx=30)

    # ------------------------------------------------------------------ #
    #  SIDEBAR + CONTENT AREA                                             #
    # ------------------------------------------------------------------ #
    def _build_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.SIDEBAR_COLOR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="MENU", font=("Arial", 9, "bold"),
                 bg=self.SIDEBAR_COLOR, fg="#888"
                 ).pack(anchor="w", padx=20, pady=(25, 5))

        self._menu_btn("📊  My Attendance",    self.show_attendance)
        self._menu_btn("📝  Apply for Leave",  self.show_leave_apply)
        self._menu_btn("📋  My Leave History", self.show_leave_history)
        self._menu_btn("⚙️  Edit My Profile",  self.show_edit_profile)

        # Content area — views are rendered inside here
        self.content_area = tk.Frame(self.root, bg=self.BG_COLOR)
        self.content_area.pack(side="right", fill="both", expand=True)

    def _menu_btn(self, text, command):
        btn = tk.Button(
            self.sidebar, text=text, font=("Arial", 11),
            bg=self.SIDEBAR_COLOR, fg="white", bd=0,
            activebackground="#2d2f39", activeforeground=self.PRIMARY_COLOR,
            anchor="w", padx=20, pady=12, cursor="hand2",
            command=lambda: self._switch(command)
        )
        btn.pack(fill="x", pady=2)

    def _switch(self, command):
        """Clear content area then load the new view."""
        if self.content_area.winfo_exists():
            for w in self.content_area.winfo_children():
                w.destroy()
        command()

    # ------------------------------------------------------------------ #
    #  ROUTING — each delegates to its own module                         #
    # ------------------------------------------------------------------ #
    def show_attendance(self):
        student_attendance.show_attendance(self.content_area, self.student_id)

    def show_leave_apply(self):
        student_leave_apply.show_leave_apply(self.content_area, self.student_id)

    def show_leave_history(self):
        student_leave_history.show_leave_history(self.content_area, self.student_id)

    def show_edit_profile(self):
        student_edit_profile.show_edit_profile(self.content_area, self.student_id)

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #
    def _get_student_name(self):
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(
                "SELECT CONCAT(first_name, ' ', last_name) "
                "FROM student_profiles WHERE student_id = %s",
                (self.student_id,))
            result = cursor.fetchone()
            db.close()
            return result[0] if result else "Student"
        except Exception:
            return "Student"
