import tkinter as tk
from tkinter import messagebox
import cv2
import os
from db_config import get_db_connection

# --- Login Logic ---

def validate_password_login(username, password, window):
    """Checks credentials against the MySQL 'admins' table."""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Check if username and password match in the database
        query = "SELECT * FROM admins WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        db.close()

        if result:
            print(f"✅ Login successful for user: {username}")
            launch_main(window)
        # Emergency Fallback (Useful for your first login before setting up DB)
        elif username == "admin" and password == "admin123":
            print("⚠️ Using hardcoded fallback login.")
            launch_main(window)
        else:
            messagebox.showerror("Error", "Invalid Username or Password")
            
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        # Fallback if MySQL/XAMPP is down during your demo
        if username == "admin" and password == "admin123":
            launch_main(window)
        else:
            messagebox.showerror("Connection Error", "Could not connect to Database. Check XAMPP.")

def validate_face_login(window):
    """Activates camera using ONLY the AdminTrainner.yml file."""
    trainer_path = "TrainingImageLabel" + os.sep + "AdminTrainner.yml"
    
    if not os.path.exists(trainer_path):
        messagebox.showerror("Error", "Admin Face Data not found!\nPlease use the 'Register Admin' button in the dashboard first.")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(trainer_path)
    face_cascade = cv2.CascadeClassifier("haarcascade_default.xml")
    
    cap = cv2.VideoCapture(0)
    found_admin = False
    
    # Give the user 10 seconds to show their face
    start_time = os.times().elapsed
    while True: 
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            predicted_id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            
            # Lower confidence = better match
            if conf < 50: 
                found_admin = True
                break
        
        cv2.imshow("Secure Face Login", frame)
        if cv2.waitKey(1) == ord('q') or found_admin:
            break
            
    cap.release()
    cv2.destroyAllWindows()

    if found_admin:
        messagebox.showinfo("Success", "Admin Identity Verified!")
        launch_main(window)
    else:
        messagebox.showwarning("Access Denied", "Face not recognized as an Administrator.")

def launch_main(window):
    """Closes login and launches dashboard."""
    window.destroy()
    import main
    # Ensure main.py has the launch_dashboard() function defined
    main.launch_dashboard()

# --- UI Setup ---
# (Your login_page() code remains identical to the template)
# --- UI Setup ---

def login_page():
    root = tk.Tk()
    root.title("Attendance System - Secure Login")
    root.geometry("900x550")
    root.configure(bg="#f0f2f5")

    # Left Frame (Visual side matching your screenshot)
    left_frame = tk.Frame(root, bg="#3498db", width=450)
    left_frame.pack(side="left", fill="both", expand=True)
    
    # You can place your blue graphic here or use a label
    tk.Label(left_frame, text="🔒", font=("Arial", 80), bg="#3498db", fg="white").pack(pady=(100, 10))
    tk.Label(left_frame, text="SECURE ACCESS", font=("Arial", 25, "bold"), bg="#3498db", fg="white").pack()

    # Right Frame (Input side)
    right_frame = tk.Frame(root, bg="white", width=450)
    right_frame.pack(side="right", fill="both", expand=True)

    tk.Label(right_frame, text="System Login", font=("Arial", 22, "bold"), bg="white").pack(pady=(50, 30))

    # Input Fields
    tk.Label(right_frame, text="Username", bg="white", fg="gray").pack(anchor="w", padx=60)
    user_ent = tk.Entry(right_frame, font=("Arial", 12), bg="#e8f0fe", bd=0)
    user_ent.pack(fill="x", padx=60, pady=5, ipady=8)

    tk.Label(right_frame, text="Password", bg="white", fg="gray").pack(anchor="w", padx=60, pady=(10, 0))
    pass_ent = tk.Entry(right_frame, font=("Arial", 12), bg="#e8f0fe", bd=0, show="*")
    pass_ent.pack(fill="x", padx=60, pady=5, ipady=8)

    # Buttons
    btn_login = tk.Button(right_frame, text="Sign In", bg="#00d2ff", fg="white", 
                          font=("Arial", 12, "bold"), bd=0, cursor="hand2",
                          command=lambda: validate_password_login(user_ent.get(), pass_ent.get(), root))
    btn_login.pack(fill="x", padx=60, pady=(30, 10), ipady=5)

    btn_face = tk.Button(right_frame, text="Sign In With Face Id", bg="white", fg="#3498db", 
                         font=("Arial", 11, "bold"), bd=1, relief="solid", cursor="hand2",
                         command=lambda: validate_face_login(root))
    btn_face.pack(fill="x", padx=60, pady=10, ipady=5)

    root.mainloop()

if __name__ == "__main__":
    login_page()