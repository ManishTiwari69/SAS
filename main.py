import tkinter as tk
from tkinter import messagebox
import admin_register
import student_register
import recognize
import view_attendance 
import check_camera

def launch_dashboard():
    window = tk.Tk()
    window.title("Dashboard - AI Attendance System")
    window.geometry("700x600")
    window.configure(background='#2c3e50')

    tk.Label(window, text="MAIN CONTROL PANEL", bg="#2c3e50", fg="white", 
             font=('Arial', 25, 'bold')).pack(pady=30)

    btn_style = {"font": ('Arial', 12, 'bold'), "fg": "white", "width": 40, "height": 2}

    # Commands link to our new files
    tk.Button(window, text="1. Check Camera System", command=check_camera.camer, 
              bg="#34495e", **btn_style).pack(pady=5)
    
    tk.Button(window, text="2. Register NEW ADMIN (Face Login)", 
              command=admin_register.register_admin, bg="#f39c12", **btn_style).pack(pady=5)
    
    tk.Button(window, text="3. Register NEW STUDENT", 
              command=student_register.register_student, bg="#27ae60", **btn_style).pack(pady=5)
    
    tk.Button(window, text="4. Start Attendance (Face Recognition)", 
              command=recognize.recognize_attendence, bg="#2980b9", **btn_style).pack(pady=5)
    
    tk.Button(window, text="5. View Records", command=view_attendance.show_attendance, 
              bg="#8e44ad", **btn_style).pack(pady=5)

    tk.Button(window, text="EXIT SYSTEM", command=window.destroy, 
              bg="#c0392b", **btn_style).pack(pady=20)

    window.mainloop()

if __name__ == "__main__":
    import login
    login.login_page()