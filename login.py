import tkinter as tk
from tkinter import messagebox
import cv2
import os
from PIL import Image, ImageTk
from db_config import get_db_connection

class LoginApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Attendance System - Secure Login")
        self.root.geometry("900x550")
        self.root.configure(bg="#f0f2f5")
        
        self.cap = None
        self.is_camera_on = False
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_cascade = cv2.CascadeClassifier("haarcascade_default.xml")

        # --- UI Setup ---
        self.left_frame = tk.Frame(self.root, bg="#3498db", width=450)
        self.left_frame.pack(side="left", fill="both", expand=True)
        
        self.video_label = tk.Label(self.left_frame, bg="#3498db")
        self.video_label.pack(expand=True, fill="both")
        
        self.icon_lbl = tk.Label(self.video_label, text="🔒", font=("Arial", 80), bg="#3498db", fg="white")
        self.icon_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.status_lbl = tk.Label(self.video_label, text="SECURE ACCESS", font=("Arial", 20, "bold"), bg="#3498db", fg="white")
        self.status_lbl.place(relx=0.5, rely=0.6, anchor="center")

        self.right_frame = tk.Frame(self.root, bg="white", width=450)
        self.right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.right_frame, text="System Login", font=("Arial", 22, "bold"), bg="white").pack(pady=(50, 30))

        tk.Label(self.right_frame, text="Username", bg="white", fg="gray").pack(anchor="w", padx=60)
        self.user_ent = tk.Entry(self.right_frame, font=("Arial", 12), bg="#e8f0fe", bd=0)
        self.user_ent.pack(fill="x", padx=60, pady=5, ipady=8)

        tk.Label(self.right_frame, text="Password", bg="white", fg="gray").pack(anchor="w", padx=60, pady=(10, 0))
        self.pass_ent = tk.Entry(self.right_frame, font=("Arial", 12), bg="#e8f0fe", bd=0, show="*")
        self.pass_ent.pack(fill="x", padx=60, pady=5, ipady=8)

        tk.Button(self.right_frame, text="Sign In", bg="#00d2ff", fg="white", font=("Arial", 12, "bold"), 
                  bd=0, cursor="hand2", command=self.handle_password_login).pack(fill="x", padx=60, pady=(30, 10), ipady=5)

        tk.Button(self.right_frame, text="Sign In With Face ID", bg="white", fg="#3498db", font=("Arial", 11, "bold"), 
                  bd=1, relief="solid", cursor="hand2", command=self.toggle_face_login).pack(fill="x", padx=60, pady=10, ipady=5)

    def toggle_face_login(self):
        trainer_path = "TrainingImageLabel/AdminTrainner.yml"
        if not os.path.exists(trainer_path):
            messagebox.showerror("Error", "No Admin Face Data found!")
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

    def update_camera_frame(self):
        if self.is_camera_on:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    predicted_id, conf = self.recognizer.predict(gray[y:y+h, x:x+w])
                    
                    if conf < 50:
                        # Draw a green box to show recognition was successful
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        self.status_lbl.config(text="Verified! Welcome.", fg="#2ecc71")
                        self.root.update()
                        
                        # Close camera and move to dashboard after a tiny delay
                        self.root.after(500, self.launch_main)
                        return # Exit the function immediately

    def stop_camera(self):
        self.is_camera_on = False
        if self.cap: self.cap.release()
        self.video_label.config(image='')
        self.icon_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.status_lbl.config(text="SECURE ACCESS")

    def handle_password_login(self):
        u, p = self.user_ent.get(), self.pass_ent.get()
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (u, p))
            
            if cursor.fetchone() or (u == "admin" and p == "admin123"):
                # Change the UI text to show progress
                self.status_lbl.config(text="Login Successful! Redirecting...", fg="#2ecc71")
                self.root.update() # Force UI to show the message
                self.root.after(800, self.launch_main) # Wait 800ms then redirect
            else:
                messagebox.showerror("Error", "Invalid Credentials")
            db.close()
        except Exception as e:
            # Fallback for demo if DB is off
            if u == "admin" and p == "admin123":
                self.launch_main()
            else:
                messagebox.showerror("Connection Error", "Check XAMPP/Database")

    def launch_main(self):
        self.stop_camera()
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Load Dashboard from main.py
        import main
        main.render_dashboard(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LoginApp()
    app.run()