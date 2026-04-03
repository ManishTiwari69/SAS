import tkinter as tk
import admin_register
import student_register
import recognize
import view_attendance 
import check_camera

def render_dashboard(window):
    window.title("Dashboard - AI Attendance System")
    window.geometry("800x650")
    window.configure(background='#2c3e50')

    tk.Label(window, text="MAIN CONTROL PANEL", bg="#2c3e50", fg="white", 
             font=('Arial', 25, 'bold')).pack(pady=40)

    btn_frame = tk.Frame(window, bg="#2c3e50")
    btn_frame.pack(expand=True)

    btn_style = {"font": ('Arial', 12, 'bold'), "fg": "white", "width": 45, "height": 2, "bd": 0, "cursor": "hand2"}

    tk.Button(btn_frame, text="1. Check Camera System", command=check_camera.camer, bg="#34495e", **btn_style).pack(pady=10)
    tk.Button(btn_frame, text="2. Register NEW ADMIN", command=admin_register.register_admin, bg="#f39c12", **btn_style).pack(pady=10)
    tk.Button(btn_frame, text="3. Register NEW STUDENT", command=student_register.register_student, bg="#27ae60", **btn_style).pack(pady=10)
    tk.Button(btn_frame, text="4. Start Attendance", command=recognize.recognize_attendence, bg="#2980b9", **btn_style).pack(pady=10)
    tk.Button(btn_frame, text="5. View Records", command=view_attendance.show_attendance, bg="#8e44ad", **btn_style).pack(pady=10)

    tk.Button(window, text="EXIT SYSTEM", command=window.destroy, bg="#c0392b", **btn_style).pack(pady=30)