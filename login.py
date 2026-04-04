import tkinter as tk
from tkinter import messagebox
import cv2
import os
import bcrypt  # Import the hashing library
from PIL import Image, ImageTk
from db_config import get_db_connection
from session import user_session  # Import the session instance

class LoginApp:
    def __init__(self, existing_root=None):
        if existing_root:
            self.root = existing_root
        else:
            self.root = tk.Tk()
            self.root.title("Attendance System - Secure Login")
            self.root.geometry("1300x850")
            self.root.resizable(True, True)

    # 2. IMPORTANT: Clear EVERYTHING currently inside the window
    # This removes the "AdminDashboard" skeletons before drawing the login
        for widget in self.root.winfo_children():
            widget.destroy()

    # 3. Setup variables
        self.cap = None
        self.is_camera_on = False


        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_cascade = cv2.CascadeClassifier("haarcascade_default.xml")

        # --- UI Setup (Same as yours) ---
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


        if user_session.login_message:
            self.status_lbl.config(text=user_session.login_message, fg="#e74c3c")
            # Clear it so it doesn't show up again on a fresh start
            user_session.login_message = ""


    # --- UPDATED: SECURE PASSWORD CHECK ---
    def handle_password_login(self):
        u, p = self.user_ent.get(), self.pass_ent.get()
        
        # Hardcoded Dev Fallback
        if u == "admin" and p == "admin123":
            self.launch_main()
            return

        try:
            db = get_db_connection()
            cursor = db.cursor()
            # 1. Only fetch by username. Don't check password in SQL!
            cursor.execute("SELECT password FROM admins WHERE username = %s", (u,))
            result = cursor.fetchone()
            
            if result:
                stored_hashed_pw = result[0]
                
                # 2. Use bcrypt to verify the plain input 'p' against the stored hash
                # We encode to utf-8 because bcrypt works with bytes
                if bcrypt.checkpw(p.encode('utf-8'), stored_hashed_pw.encode('utf-8')):
                    self.status_lbl.config(text="Login Successful! Redirecting...", fg="#2ecc71")
                    self.root.update()
                    self.root.after(800, self.launch_main)
                else:
                    messagebox.showerror("Error", "Invalid Password")
            else:
                messagebox.showerror("Error", "Username not found")
            
            db.close()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Database error: {e}")

    # --- FIXED: CAMERA LOOP ---
    def update_camera_frame(self):
        if self.is_camera_on:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                
                for (x, y, w, h) in faces:
                    predicted_id, conf = self.recognizer.predict(gray[y:y+h, x:x+w])
                    
                    # Confidence < 100 is usually good, 50 is very strict
                    if conf < 65: 
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        self.status_lbl.config(text="Verified! Welcome.", fg="#2ecc71")
                        self.root.update()
                        self.root.after(500, self.launch_main)
                        return 
                    else:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)

                # Convert frame to PhotoImage for Tkinter
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((450, 450), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            
            # This line is CRITICAL to keep the camera running
            self.root.after(10, self.update_camera_frame)

    # --- REST OF YOUR FUNCTIONS ---
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

    def stop_camera(self):
        self.is_camera_on = False
        if self.cap: self.cap.release()
        self.video_label.config(image='')
        self.icon_lbl.place(relx=0.5, rely=0.4, anchor="center")
        self.status_lbl.config(text="SECURE ACCESS", fg="white")

    def launch_main(self):
    # 1. Kill the camera so it doesn't hang in the background
        self.stop_camera()
        
        # 2. Update the session so Main.py lets us in
        user_session.is_logged_in = True
        user_session.current_user = self.user_ent.get() if self.user_ent.get() else "Admin"

        # 3. CRITICAL: Wipe the window clean before importing Main
        for widget in self.root.winfo_children():
            widget.destroy()

        # 4. Import using the EXACT filename (usually lowercase 'main')
        try:
            import main 
            main.render_dashboard(self.root)
        except ModuleNotFoundError:
            # If your file is definitely 'Main.py', use this instead:
            import Main
            Main.render_dashboard(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LoginApp()
    app.run()