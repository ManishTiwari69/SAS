import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import cv2
import os
import shutil
import bcrypt
from db_config import get_db_connection
from train_image import TrainImages 

UPLOAD_DIR = "Student_Profiles"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def register_student(container):
    # 1. Clear the content area
    for widget in container.winfo_children():
        widget.destroy()

    # REMOVED: container.title, container.geometry, container.configure
    # These belonged to the root window; the Dashboard handles them now.

    # Variables for Face Capture
    is_capturing = [False]
    cap = [None]
    sample_count = [0]
    face_detector = cv2.CascadeClassifier("haarcascade_default.xml")
    selected_pic_relative_path = tk.StringVar()

    # --- Header (Inside the container) ---
    header = tk.Frame(container, bg="#2c3e50", height=60)
    header.pack(side="top", fill="x")
    tk.Label(header, text="🎓 NEW STUDENT ENROLLMENT", font=("Arial", 16, "bold"), 
             bg="#2c3e50", fg="white").pack(pady=15)

    # --- Main Container ---
    main_frame = tk.Frame(container, bg="#f4f7f6")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # LEFT COLUMN (Scrollable Form)
    left_column = tk.Frame(main_frame, bg="#f4f7f6", width=500)
    left_column.pack(side="left", fill="both", expand=True, padx=5)

    canvas = tk.Canvas(left_column, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_column, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    ents = {}

    def add_section(text):
        lbl = tk.Label(scrollable_frame, text=text, font=("Arial", 11, "bold"), bg="#ecf0f1", fg="#2c3e50", anchor="w")
        lbl.pack(fill="x", pady=(15, 5), ipady=3)

    def create_row(label, is_pass=False):
        row = tk.Frame(scrollable_frame, bg="white")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, bg="white", width=20, anchor="w").pack(side="left", padx=5)
        entry = tk.Entry(row, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        return entry

    # --- 1. Personal Info ---
    add_section("1. Personal Information")
    ents['fname'] = create_row("First Name:")
    ents['mname'] = create_row("Middle Name:")
    ents['lname'] = create_row("Last Name:")
    
    dob_row = tk.Frame(scrollable_frame, bg="white")
    dob_row.pack(fill="x", pady=2)
    tk.Label(dob_row, text="Date of Birth:", bg="white", width=20, anchor="w").pack(side="left", padx=5)
    ents['dob'] = DateEntry(dob_row, background='darkblue', foreground='white', borderwidth=2)
    ents['dob'].pack(side="left", padx=5)

    gender_row = tk.Frame(scrollable_frame, bg="white")
    gender_row.pack(fill="x", pady=2)
    tk.Label(gender_row, text="Gender:", bg="white", width=20, anchor="w").pack(side="left", padx=5)
    gender_var = tk.StringVar(value="Male")
    ents['gender_var'] = gender_var # Store in ents for DB access
    ttk.Combobox(gender_row, textvariable=gender_var, values=["Male", "Female", "Other"]).pack(side="left", padx=5)

    # --- 2. Contact Info ---
    add_section("2. Contact Information")
    ents['curr_addr'] = create_row("Current Address:")
    ents['perm_addr'] = create_row("Permanent Address:")
    ents['phone'] = create_row("Mobile Number:")
    ents['email'] = create_row("Email Address:")

    # --- 3. Academic Details ---
    add_section("3. Academic Details")
    ents['year'] = create_row("Academic Year (e.g. 2026):")
    ents['faculty'] = create_row("Faculty:")
    ents['course'] = create_row("Course:")

    # --- 4. Emergency Contact ---
    add_section("4. Parent/Guardian Details")
    ents['p_name'] = create_row("Guardian Name:")
    ents['p_phone'] = create_row("Guardian Phone:")
    ents['p_rel'] = create_row("Relationship:")

    # --- 5. Technical Details ---
    add_section("5. Account & Security")
    ents['user'] = create_row("Set Username:")
    ents['pass'] = create_row("Set Password:", is_pass=True)

    consent_var = tk.IntVar()
    tk.Checkbutton(scrollable_frame, text="I declare that the information provided is correct.", 
                    variable=consent_var, bg="white").pack(pady=10)

    # RIGHT COLUMN (Face Capture & Photo)
    right_column = tk.Frame(main_frame, bg="#f4f7f6")
    right_column.pack(side="right", fill="both", expand=True, padx=10)

    preview_lbl = tk.Label(right_column, text="Profile Photo", bg="#dfe6e9", width=20, height=10)
    preview_lbl.pack(pady=5)

    def upload_image():
        abs_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png")])
        if abs_path:
            filename = f"{ents['user'].get() or 'student'}_profile{os.path.splitext(abs_path)[1]}"
            dest_path = os.path.join(UPLOAD_DIR, filename)
            shutil.copy(abs_path, dest_path)
            img = Image.open(dest_path).resize((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            preview_lbl.config(image=photo, text="")
            preview_lbl.image = photo
            selected_pic_relative_path.set(dest_path.replace("\\", "/"))

    tk.Button(right_column, text="📁 Upload Official Photo", command=upload_image, bg="#34495e", fg="white").pack(fill="x", pady=5)

    cam_box = tk.LabelFrame(right_column, text="Biometric Enrollment", bg="white")
    cam_box.pack(fill="both", expand=True, pady=10)
    video_lbl = tk.Label(cam_box, bg="black")
    video_lbl.pack(fill="both", expand=True, padx=5, pady=5)

    def update_capture_feed():
        if is_capturing[0] and sample_count[0] < 100:
            ret, frame = cap[0].read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    sample_count[0] += 1
                    if not os.path.exists("StudentTrainingImage"): os.makedirs("StudentTrainingImage")
                    cv2.imwrite(f"StudentTrainingImage/{ents['user'].get()}.{sample_count[0]}.jpg", gray[y:y+h, x:x+w])
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((350, 250), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                video_lbl.imgtk = imgtk
                video_lbl.configure(image=imgtk)
                
                if sample_count[0] < 100:
                    container.after(10, update_capture_feed)
                else:
                    save_to_db()

    def start_registration():
        if not ents['user'].get() or not ents['pass'].get():
            messagebox.showerror("Error", "Username and Password are required!")
            return
        if consent_var.get() == 0:
            messagebox.showerror("Error", "Please check the declaration box.")
            return
        is_capturing[0] = True
        cap[0] = cv2.VideoCapture(0)
        update_capture_feed()

    def save_to_db():
        is_capturing[0] = False
        if cap[0]: cap[0].release()
        
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            password_plain = ents['pass'].get()
            hashed = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("INSERT INTO students (username, password) VALUES (%s, %s)", 
                           (ents['user'].get(), hashed))
            s_id = cursor.lastrowid 

            profile_sql = """INSERT INTO student_profiles 
                             (student_id, first_name, middle_name, last_name, dob, gender, phone, email, curr_address, perm_address, photo_path) 
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            
            profile_data = (s_id, ents['fname'].get(), ents['mname'].get(), ents['lname'].get(), 
                            ents['dob'].get_date(), ents['gender_var'].get(), ents['phone'].get(), 
                            ents['email'].get(), ents['curr_addr'].get(), ents['perm_addr'].get(), 
                            selected_pic_relative_path.get())
            
            cursor.execute(profile_sql, profile_data)

            academic_sql = """INSERT INTO student_academic 
                              (student_id, acad_year, faculty, course, guardian_name, guardian_phone, relationship) 
                              VALUES (%s,%s,%s,%s,%s,%s,%s)"""
            
            academic_data = (s_id, ents['year'].get(), ents['faculty'].get(), ents['course'].get(), 
                             ents['p_name'].get(), ents['p_phone'].get(), ents['p_rel'].get())
            
            cursor.execute(academic_sql, academic_data)

            try:
                TrainImages(new_id=s_id, training_type="student")
            except Exception as e:
                print(f"Training failed: {e}") 
            # --------------------------

            messagebox.showinfo("Success", f"Student {ents['fname'].get()} registered and trained successfully!")
            back_to_dash()

        except Exception as e:
            if 'db' in locals():
                db.rollback() 
            messagebox.showerror("Database Error", f"Could not save: {str(e)}")

    # Footer
    footer = tk.Frame(container, bg="#f4f7f6")
    footer.pack(side="bottom", fill="x", pady=10)

    def back_to_dash():
        if cap[0]: cap[0].release()
        # Find the root window (tk.Tk) from the container
        root = container.winfo_toplevel()
        import main
        # Passing root to render_dashboard as expected by your login logic
        main.render_dashboard(root)

    tk.Button(footer, text="⬅ Cancel", command=back_to_dash, bg="#95a5a6", fg="white", width=15).pack(side="left", padx=40)
    tk.Button(footer, text="🚀 ENROLL STUDENT", command=start_registration, bg="#2980b9", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="right", padx=40)