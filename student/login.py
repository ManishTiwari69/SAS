import sys
import os
import tkinter as tk
from tkinter import messagebox
import cv2
import bcrypt
from PIL import Image, ImageTk

# --- FIX: Add the parent directory to sys.path so Python can find db_config, session, etc. ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import normally without the ".." dots
from db_config import get_db_connection
from session import user_session 
from validate import Validator

class StudentLoginApp:
    def __init__(self, existing_root=None):
        if existing_root:
            self.root = existing_root
            self.root.geometry("1300x850")
        else:
            self.root = tk.Tk()
            self.root.title("Attendance System - Student Login")
            self.root.geometry("1300x850")
            self.root.resizable(True, True)

        for widget in self.root.winfo_children():
            widget.destroy()

        self.cap = None
        self.is_camera_on = False
        self.logged_in_id = None

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        # Ensure path to xml is correct based on where you run the script
        self.face_cascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(__file__), "..", "haarcascade_default.xml"))

        # --- UI Setup ---
        self.left_frame = tk.Frame(self.root, bg="#2c3e50", width=450) 
        self.left_frame.pack(side="left", fill="both", expand=True)
        
        self.video_label = tk.Label(self.left_frame, bg="#2c3e50")
        self.video_label.pack(expand=True, fill="both")
        
        self.icon_lbl = tk.Label(self.video_label, text="🎓", font=("Arial", 80), bg="#2c3e50", fg="white")
        self.icon_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.status_lbl = tk.Label(self.video_label, text="STUDENT ACCESS", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white")
        self.status_lbl.place(relx=0.5, rely=0.6, anchor="center")

        self.right_frame = tk.Frame(self.root, bg="white", width=450)
        self.right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.right_frame, text="Student Login", font=("Arial", 22, "bold"), bg="white").pack(pady=(50, 30))

        tk.Label(self.right_frame, text="Username", bg="white", fg="gray").pack(anchor="w", padx=60)
        self.user_ent = tk.Entry(self.right_frame, font=("Arial", 12), bg="#f4f7f6", bd=0)
        self.user_ent.pack(fill="x", padx=60, pady=5, ipady=8)

        tk.Label(self.right_frame, text="Password", bg="white", fg="gray").pack(anchor="w", padx=60, pady=(10, 0))
        self.pass_ent = tk.Entry(self.right_frame, font=("Arial", 12), bg="#f4f7f6", bd=0, show="*")
        self.pass_ent.pack(fill="x", padx=60, pady=5, ipady=8)

        tk.Button(self.right_frame, text="Sign In", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), 
                  bd=0, cursor="hand2", command=self.handle_password_login).pack(fill="x", padx=60, pady=(30, 10), ipady=5)

        tk.Button(self.right_frame, text="Sign In With Face ID", bg="white", fg="#27ae60", font=("Arial", 11, "bold"), 
                  bd=1, relief="solid", cursor="hand2", command=self.toggle_face_login).pack(fill="x", padx=60, pady=10, ipady=5)

        if user_session.login_message:
            self.status_lbl.config(text=user_session.login_message, fg="#e74c3c")
            user_session.login_message = ""

    def handle_password_login(self):
        u, p = self.user_ent.get(), self.pass_ent.get()
        if Validator.is_empty({"Username": u, "Password": p}):
            return 

        try:
            db = get_db_connection()
            cursor = db.cursor()
            # Select status as well
            cursor.execute("SELECT student_id, password, username, status FROM students WHERE username = %s", (u,))
            result = cursor.fetchone()
            
            if result:
                db_student_id, stored_hashed_pw, student_name, status = result
                
                # Check status first
                if str(status).lower() != 'active':
                    messagebox.showwarning("Access Denied", "Your account is currently deactivated.")
                    return

                if bcrypt.checkpw(p.encode('utf-8'), stored_hashed_pw.encode('utf-8')):
                    self.logged_in_id = db_student_id 
                    user_session.current_user = student_name
                    self.status_lbl.config(text="Login Successful!", fg="#2ecc71")
                    self.root.update()
                    self.root.after(800, self.launch_student_dashboard)
                else:
                    messagebox.showerror("Error", "Invalid Password")
            else:
                messagebox.showerror("Error", "Student Username not found")
            db.close()
        except Exception as e:
            messagebox.showerror("Database Error", f"Error: {e}")

    def update_camera_frame(self):
        if self.is_camera_on:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                
                for (x, y, w, h) in faces:
                    predicted_id, conf = self.recognizer.predict(gray[y:y+h, x:x+w])
                    
                    if conf < 65: 
                        # --- FIX: Only query DB if we haven't already identified a student ---
                        if not self.logged_in_id: 
                            try:
                                db = get_db_connection()
                                cursor = db.cursor()
                                cursor.execute("SELECT username, status FROM students WHERE student_id = %s", (predicted_id,))
                                result = cursor.fetchone()
                                db.close()

                                if result:
                                    student_name, status = result
                                    if str(status).lower() == 'active':
                                        self.logged_in_id = predicted_id 
                                        user_session.current_user = student_name
                                        self.status_lbl.config(text="Face Verified! Welcome.", fg="#2ecc71")
                                        
                                        # Stop the camera immediately on success
                                        self.is_camera_on = False
                                        self.cap.release()
                                        
                                        self.root.after(500, self.launch_student_dashboard)
                                        return 
                                    else:
                                        self.status_lbl.config(text="Account Deactivated", fg="#e74c3c")
                            except Exception as e:
                                print(f"Face ID DB Check Error: {e}")
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

                # ... (rest of your image rendering code)
                self.root.after(10, self.update_camera_frame)


    def toggle_face_login(self):
        # Look for trainer in the parent directory's folder
        trainer_path = os.path.join(os.path.dirname(__file__), "..", "TrainingImageLabel", "StudentTrainner.yml")
        if not os.path.exists(trainer_path):
            messagebox.showerror("Error", "No Student Face Data found!")
            return

        if not self.is_camera_on:
            self.recognizer.read(trainer_path)
            self.cap = cv2.VideoCapture(0)
            self.is_camera_on = True
            self.icon_lbl.place_forget()
            self.status_lbl.config(text="Scanning Face...")
            self.update_camera_frame()
        else:
            self.stop_camera()

    def stop_camera(self):
        self.is_camera_on = False
        if self.cap: self.cap.release()
        self.video_label.config(image='')
        self.icon_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.status_lbl.config(text="STUDENT ACCESS", fg="white")

    def launch_student_dashboard(self):
        self.stop_camera()
        user_session.is_logged_in = True
        for widget in self.root.winfo_children():
            widget.destroy()

        try:
            import student_dashboard
            student_dashboard.StudentDashboard(self.root, student_id=self.logged_in_id)
        except Exception as e:
            messagebox.showerror("App Error", f"Could not load dashboard: {e}")

    def run(self):
        self.root.mainloop()

# --- FIX: Call the App class, not the Dashboard class ---
if __name__ == "__main__":
    app = StudentLoginApp()
    app.run()