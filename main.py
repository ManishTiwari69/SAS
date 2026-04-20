"""
main.py  —  AdminDashboard
───────────────────────────
Security
  • If launched directly WITHOUT a valid session → forcibly redirects to login.
  • Role-based sidebar: Teacher sees student features; Super sees everything.

Usage
  Always launched through login.py, which sets user_session before calling:
      AdminDashboard(root, admin_id=logged_in_id)
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date
import sys, os

from db_config       import get_db_connection, check_db_status
from session         import user_session

# ── lazy imports (avoids circular issues at module load) ───────────────
import check_camera
import admin_register
import recognize
import view_attendance
import manage_students          # NEW — both roles
import manage_admins            # Super only
from edit_admin      import edit_admin
from student_register import register_student
import update_student


class AdminDashboard:
    # ── colours ────────────────────────────────────────────────────────
    SIDEBAR  = "#1a1c23"
    PRIMARY  = "#00d084"
    ACCENT   = "#e74c3c"
    BG       = "#f8f9fa"

    def __init__(self, root, admin_id):
        self.root     = root
        self.admin_id = admin_id

        print(f"DEBUG: Loaded role is '{user_session.current_role}'")

        # ══ SESSION BARRIER ═══════════════════════════════════════════
        # Executed BEFORE any widget is created — catches both direct
        # python main.py runs AND internal navigation without a session.
        if not user_session.is_logged_in:
            self._redirect_to_login()
            return
        # ══════════════════════════════════════════════════════════════

        self.role       = user_session.current_role   # 'Super' | 'Teacher'
        self.admin_name = self._get_admin_name()

        self.root.title("Attenad — AI Attendance System")
        self.root.geometry("1300x850")
        self.root.configure(bg=self.BG)

        # Intercept window-close button  → clean logout
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()

    # ──────────────────────────────────────────────────────────────────
    #  LAYOUT
    # ──────────────────────────────────────────────────────────────────
    def _build_layout(self):

        # ── Sidebar ───────────────────────────────────────────────────
        self.sidebar = tk.Frame(self.root, bg=self.SIDEBAR, width=245)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = tk.Frame(self.sidebar, bg=self.SIDEBAR)
        logo.pack(fill="x", pady=(26, 6))
        tk.Label(logo, text="🅰  Attenad",
                 font=("Arial", 19, "bold"),
                 bg=self.SIDEBAR, fg=self.PRIMARY).pack()

        badge_color = self.PRIMARY if self.role == "Super" else "#3498db"
        tk.Label(logo,
                 text=f"● {self.role} Admin",
                 font=("Arial", 9, "bold"),
                 bg=self.SIDEBAR, fg=badge_color).pack(pady=(2, 6))

        tk.Frame(self.sidebar, bg="#2d2f39", height=1).pack(fill="x", padx=18)

        # ── Menu items ────────────────────────────────────────────────
        self._section("MAIN")
        self._btn("🏠  Dashboard",          self._render_overview)
        self._btn("📷  Check Camera",
                  lambda: check_camera.camer(
                      self.content, self._render_overview))
        self._btn("🛡️  Recognize",
                  lambda: recognize.recognize_attendance(
                      self.root, self._render_overview))
        self._btn("📊  Attendance Records",
                  lambda: view_attendance.show_attendance(self.content))

        self._section("STUDENTS")
        self._btn("👨‍🎓  Register Student",
                  lambda: register_student(self.content, self._render_overview))
        self._btn("✏️  Update Student",
                  lambda: update_student.update_student(self.content))
        self._btn("📋  Manage Students",          # ← NEW (both roles)
                  lambda: manage_students.show_manage_students(self.content))

        # Super-only section
        if self.role == "Super":
            self._section("ADMINISTRATION")
            self._btn("👥  Manage Admins",
                      lambda: manage_admins.show_manage_admins(
                          self.content, self.admin_id,
                          self._render_overview))
            self._btn("🔐  Register Admin",
                      lambda: admin_register.register_admin(self.content))

        self._section("ACCOUNT")
        self._btn("⚙️  My Profile",
                  lambda: edit_admin(
                      self.content, self.admin_id, self._render_overview))
        self._btn("🚪  Logout", self._logout, color=self.ACCENT)

        # ── Topbar ────────────────────────────────────────────────────
        topbar = tk.Frame(self.root, bg="white", height=62,
                          highlightthickness=1, highlightbackground="#eee")
        topbar.pack(side="top", fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar,
                 text=f"Welcome back, {self.admin_name} 👋",
                 font=("Arial", 12, "bold"),
                 bg="white", fg="#1a1c23"
                 ).pack(side="right", padx=28, pady=18)

        tk.Label(topbar,
                 text=f"  {self.role} Admin  ",
                 font=("Arial", 9, "bold"),
                 bg=badge_color, fg="white",
                 padx=6, pady=3
                 ).pack(side="right", pady=18)

        # ── Content area ──────────────────────────────────────────────
        self.content = tk.Frame(self.root, bg=self.BG)
        self.content.pack(side="right", fill="both", expand=True)

        self._render_overview()

    def _section(self, text):
        tk.Label(self.sidebar, text=text,
                 font=("Arial", 8, "bold"),
                 bg=self.SIDEBAR, fg="#555"
                 ).pack(anchor="w", padx=22, pady=(14, 3))

    def _btn(self, text, cmd, color=None):
        fg = color or "white"

        def _wrapper():
            if self.content.winfo_exists():
                for w in self.content.winfo_children():
                    w.destroy()
                cmd()

        tk.Button(
            self.sidebar, text=f"  {text}",
            font=("Arial", 10),
            bg=self.SIDEBAR, fg=fg, bd=0,
            activebackground="#2d2f39",
            activeforeground=self.PRIMARY,
            anchor="w", padx=20, pady=10,
            cursor="hand2", command=_wrapper
        ).pack(fill="x", pady=1)

    # ──────────────────────────────────────────────────────────────────
    #  OVERVIEW
    # ──────────────────────────────────────────────────────────────────
    def _render_overview(self):
        for w in self.content.winfo_children():
            w.destroy()

        stats = self._get_stats()

        # title
        title_bar = tk.Frame(self.content, bg=self.BG)
        title_bar.pack(fill="x", padx=35, pady=(26, 4))
        tk.Label(title_bar, text="Dashboard Overview",
                 font=("Arial", 18, "bold"),
                 bg=self.BG, fg="#1a1c23").pack(side="left")
        tk.Label(title_bar,
                 text=f"📅  {date.today().strftime('%A, %d %B %Y')}",
                 font=("Arial", 10), bg=self.BG, fg="#888"
                 ).pack(side="right")

        # stat cards
        cards = tk.Frame(self.content, bg=self.BG)
        cards.pack(fill="x", padx=35, pady=(10, 20))

        self._card(cards, "TOTAL STUDENTS", stats["total"],  "#fff",       "#1a1c23", "👨‍🎓", 0)
        self._card(cards, "PRESENT TODAY",  stats["present"], self.PRIMARY, "white",   "✅",  1)
        self._card(cards, "ABSENT TODAY",   stats["absent"],  "#e74c3c",   "white",   "❌",  2)
        if self.role == "Super":
            self._card(cards, "ACTIVE ADMINS", stats["admins"], "#3498db", "white", "🛡️", 3)

        # quick-action buttons
        qa = tk.LabelFrame(self.content, text="  Quick Actions  ",
                           font=("Arial", 11, "bold"),
                           bg="white", bd=1, relief="solid")
        qa.pack(fill="x", padx=35, pady=(0, 20))

        actions = [
            ("🛡️  Start Recognition", "#2c3e50",
             lambda: recognize.recognize_attendance(
                 self.root, self._render_overview)),
            ("📊  Attendance Records", "#3498db",
             lambda: view_attendance.show_attendance(self.content)),
            ("👨‍🎓  Register Student",  "#27ae60",
             lambda: register_student(self.content, self._render_overview)),
            ("📋  Manage Students",    "#8e44ad",
             lambda: manage_students.show_manage_students(self.content)),
        ]
        if self.role == "Super":
            actions.append(
                ("👥  Manage Admins", "#e67e22",
                 lambda: manage_admins.show_manage_admins(
                     self.content, self.admin_id, self._render_overview)))

        for txt, bg, cmd in actions:
            def _make(c=cmd):
                for w in self.content.winfo_children():
                    w.destroy()
                c()
            tk.Button(qa, text=txt, bg=bg, fg="white",
                      font=("Arial", 10, "bold"), relief="flat",
                      padx=18, pady=10, cursor="hand2",
                      command=_make).pack(side="left", padx=12, pady=14)

    def _card(self, parent, title, value, bg, fg, icon, col):
        card = tk.Frame(parent, bg=bg, width=210, height=118,
                        highlightthickness=1, highlightbackground="#e0e0e0")
        card.grid(row=0, column=col, padx=10)
        card.grid_propagate(False)
        tk.Label(card, text=icon,  font=("Arial", 18),
                 bg=bg, fg=fg).pack(pady=(16, 1))
        tk.Label(card, text=str(value), font=("Arial", 22, "bold"),
                 bg=bg, fg=fg).pack()
        tk.Label(card, text=title, font=("Arial", 8, "bold"),
                 bg=bg,
                 fg=fg if bg != "#fff" else "#888").pack()

    # ──────────────────────────────────────────────────────────────────
    #  DB helpers
    # ──────────────────────────────────────────────────────────────────
    def _get_stats(self):
        try:
            db     = get_db_connection()
            cursor = db.cursor()
            today  = date.today()

            cursor.execute("SELECT COUNT(*) FROM students")
            total  = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(DISTINCT student_id) FROM attendance_logs "
                "WHERE log_date=%s", (today,))
            present = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM admins WHERE status='active'")
            admins = cursor.fetchone()[0]

            db.close()
            return {"total": total, "present": present,
                    "absent": total - present, "admins": admins}
        except Exception as e:
            print(f"[stats] {e}")
            return {"total": 0, "present": 0, "absent": 0, "admins": 0}

    def _get_admin_name(self):
        try:
            db     = get_db_connection()
            cursor = db.cursor()
            cursor.execute(
                "SELECT first_name FROM admin_details WHERE admin_id=%s",
                (self.admin_id,))
            r = cursor.fetchone()
            db.close()
            return r[0] if r else "Admin"
        except Exception:
            return "Admin"

    # ──────────────────────────────────────────────────────────────────
    #  Auth
    # ──────────────────────────────────────────────────────────────────
    def _redirect_to_login(self):
        """
        Called when there is NO valid session.
        Works whether self.root already has widgets or not.
        """
        user_session.login_message = "⚠️  Please log in to continue."
        try:
            for w in self.root.winfo_children():
                w.destroy()
        except Exception:
            pass
        import login
        login.LoginApp(self.root)

    def _logout(self):
        user_session.clear()
        self._redirect_to_login()

    def _on_close(self):
        """Graceful window close — clear session then destroy."""
        user_session.clear()
        self.root.destroy()


# ──────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # 1. DB check
    if not check_db_status():
        _r = tk.Tk()
        _r.withdraw()
        messagebox.showerror(
            "Database Error",
            "Cannot connect to MySQL.\n"
            "Please start XAMPP / MySQL and try again.")
        _r.destroy()
        sys.exit(1)

    # 2. ── SESSION BARRIER (direct launch guard) ──────────────────────
    # When main.py is run directly (python main.py), no session exists.
    # We start the login flow instead of the dashboard.
    root = tk.Tk()
    root.geometry("1300x850")
    root.title("Attenad — Attendance System")

    if not user_session.is_logged_in:
        # Route straight to login — AdminDashboard will NOT be constructed
        import login
        login.LoginApp(root)
    else:
        AdminDashboard(root, admin_id=user_session.admin_id or 1)

    root.mainloop()
