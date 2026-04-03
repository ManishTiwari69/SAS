import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import cv2
import os
from PIL import Image, ImageTk
from db_config import get_db_connection
import train_image
import shutil

def register_admin():
    reg_window = tk.Toplevel()
    reg_window.title("Admin Registration - Full Profile")
    reg_window.geometry("550x800")
    reg_window.configure(bg="#f8f9fa")

    uploaded_pic_path = tk.StringVar(value="")

    # --- Header ---
    header = tk.Frame(reg_window, bg="#3498db", height=80)
    header.pack(fill="x")
    tk.Label(header, text="ADMIN REGISTRATION", font=("Arial", 16, "bold"), bg="#3498db", fg="white").pack(pady=20)

    # --- Scrollable Main Frame ---
    container = tk.Frame(reg_window, bg="#f8f9fa")
    container.pack(fill="both", expand=True, padx=20, pady=10)

    canvas = tk.Canvas(container, bg="#f8f9fa", highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#f8f9fa")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=480)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- UI Helper ---
    def create_field(parent, label_text, placeholder=""):
        frame = tk.Frame(parent, bg="#f8f9fa")
        frame.pack(fill="x", pady=5)
        tk.Label(frame, text=label_text, font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#34495e").pack(anchor="w")
        entry = tk.Entry(frame, font=("Arial", 11), bd=1, relief="flat", highlightthickness=1, highlightbackground="#dcdde1")
        entry.pack(fill="x", ipady=8, pady=2)
        if placeholder:
            entry.insert(0, placeholder)
        return entry

    # --- Form Fields ---
    user_ent = create_field(scroll_frame, "Username*")
    pass_ent = create_field(scroll_frame, "Password*")
    pass_ent.config(show="*")
    
    fname_ent = create_field(scroll_frame, "First Name")
    lname_ent = create_field(scroll_frame, "Last Name")
    
    # Date Field with clear format
    dob_ent = create_field(scroll_frame, "Date of Birth (YYYY-MM-DD)", "2000-01-01")
    
    tk.Label(scroll_frame, text="Gender", font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#34495e").pack(anchor="w", pady=(5,0))
    gender_var = tk.StringVar(value="Male")
    gender_menu = ttk.Combobox(scroll_frame, textvariable=gender_var, values=["Male", "Female", "Other"], state="readonly")
    gender_menu.pack(fill="x", ipady=5)

    addr_ent = create_field(scroll_frame, "Address")
    phone_ent = create_field(scroll_frame, "Phone No")

    # --- Upload Profile Pic Section ---
    tk.Label(scroll_frame, text="Profile Photo", font=("Arial", 10, "bold"), bg="#f8f9fa", fg="#34495e").pack(anchor="w", pady=(15,0))
    
    def upload_image():
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            uploaded_pic_path.set(file_path)
            lbl_status.config(text="Status: Image Selected ✅", fg="green")

    btn_upload = tk.Button(scroll_frame, text="📁 Upload Photo from PC", command=upload_image, bg="#ecf0f1", bd=0, cursor="hand2")
    btn_upload.pack(fill="x", pady=5, ipady=5)
    lbl_status = tk.Label(scroll_frame, text="No image selected (Camera will be used if empty)", font=("Arial", 8), bg="#f8f9fa", fg="gray")
    lbl_status.pack()

    # --- Submit Logic ---
    def submit_data():
        u, p, dob = user_ent.get(), pass_ent.get(), dob_ent.get()
        
        # Simple Date Validation
        if len(dob) != 10 or dob[4] != '-' or dob[7] != '-':
            messagebox.showerror("Format Error", "Please use YYYY-MM-DD format for date.")
            return

        if not u or not p:
            messagebox.showerror("Error", "Username and Password are required!")
            return

        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (u, p))
            admin_id = cursor.lastrowid 
            
            pic_folder = os.path.join("TrainingImage", "admin", str(admin_id))
            if not os.path.exists(pic_folder): os.makedirs(pic_folder)
            
            # Handle Uploaded Pic
            final_pic_path = os.path.join(pic_folder, "profile_pic.jpg")
            if uploaded_pic_path.get():
                shutil.copy(uploaded_pic_path.get(), final_pic_path)

            cursor.execute("""
                INSERT INTO admin_details (admin_id, first_name, last_name, dob, gender, address, phone_no, profile_pic_path) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (admin_id, fname_ent.get(), lname_ent.get(), dob, gender_var.get(), addr_ent.get(), phone_ent.get(), final_pic_path))
            
            db.commit()
            db.close()

            reg_window.destroy()
            messagebox.showinfo("Success", "Profile Saved! Opening camera for Face ID Training...")
            
            # Start camera (It will skip profile pic if already uploaded)
            capture_faces(admin_id, u, skip_profile=(uploaded_pic_path.get() != ""))
            train_image.TrainImages(new_id=admin_id, training_type="admin")
            
        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")

    # --- Final Submit Button ---
    submit_btn = tk.Button(reg_window, text="SUBMIT & START BIOMETRICS", bg="#2ecc71", fg="white", 
                           font=("Arial", 12, "bold"), bd=0, cursor="hand2", command=submit_data)
    submit_btn.pack(side="bottom", fill="x", padx=30, pady=20, ipady=12)

def capture_faces(admin_id, username, skip_profile=False):
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier("haarcascade_default.xml")
    save_path = os.path.join("TrainingImage", "admin", str(admin_id))
    
    sampleNum = 0
    profile_captured = skip_profile # If uploaded, we skip webcam profile capture
    
    if not skip_profile:
        messagebox.showinfo("Camera", "Look at the camera for your Profile Picture.")

    while True:
        ret, img = cam.read()
        if not ret: break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            if not profile_captured:
                cv2.imwrite(os.path.join(save_path, "profile_pic.jpg"), img[y:y+h, x:x+w])
                profile_captured = True

            sampleNum += 1
            cv2.imwrite(os.path.join(save_path, f"{username}.{admin_id}.{sampleNum}.jpg"), gray[y:y+h, x:x+w])
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow('Face Scanning...', img)
        if cv2.waitKey(1) & 0xFF == ord('q') or sampleNum >= 50:
            break
    cam.release()
    cv2.destroyAllWindows()