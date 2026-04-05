import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import cv2
import os
from PIL import Image, ImageTk
from db_config import get_db_connection
from train_image import TrainImages 
from validate import Validator 
import shutil

def update_student(container):
    for widget in container.winfo_children():
        widget.destroy()

    # --- 1. Variables & State ---
    is_capturing = [False]
    cap = [None]
    sample_count = [0]
    face_detector = cv2.CascadeClassifier("haarcascade_default.xml")
    ents = {}
    err_lbls = {}
    faculty_map = {
        "Management": ["BBA", "BBM", "BHM", "BTTM", "BIM"],
        "Humanities & Social Sciences": ["BA", "MA in Sociology", "Economics", "BCA"],
        "Law": ["LL.B.", "B.A.LL.B.", "LL.M."]
    }

    # --- 2. INTERNAL FUNCTIONS (Define these BEFORE building UI) ---

    def upload_profile_pic():
        sid = id_ent.get()
        username = ents['user'].get().strip()
        if not username:
            messagebox.showerror("Error", "Please set/fetch a username first!")
            return
            
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            student_folder = os.path.join("TrainingImage", "student", username)
            if not os.path.exists(student_folder): os.makedirs(student_folder)
            
            ext = os.path.splitext(file_path)[1]
            dest = os.path.join(student_folder, f"profile_{sid}{ext}")
            shutil.copy(file_path, dest)
            messagebox.showinfo("Success", "Profile picture updated!")

    def start_biometric_update():
        sid = id_ent.get()
        # Use .get() for the StringVar or Entry depending on how 'user' is stored
        username = ents['user'].get().strip() 
        
        if not sid or not username:
            messagebox.showerror("Error", "Please fetch student and ensure Username is filled!")
            return
        
        student_folder = os.path.join("TrainingImage", "student", username)
        video_lbl.configure(height=200)
        video_lbl.pack(pady=10)
        progress_lbl.pack()
        
        is_capturing[0], sample_count[0] = True, 0
        cap[0] = cv2.VideoCapture(0)

        def capture_loop():
            if is_capturing[0] and sample_count[0] < 100:
                ret, frame = cap[0].read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # Detect faces to ensure we only save face samples
                    faces = face_detector.detectMultiScale(gray, 1.3, 5)
                    
                    for (x, y, w, h) in faces:
                        sample_count[0] += 1
                        if not os.path.exists(student_folder): 
                            os.makedirs(student_folder)
                        
                        # Save the face sample
                        file_path = os.path.join(student_folder, f"{sid}.{sample_count[0]}.jpg")
                        cv2.imwrite(file_path, gray[y:y+h, x:x+w])
                        
                        # Draw rectangle for visual feedback
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Update Progress Text
                    progress_lbl.config(text=f"Capturing: {sample_count[0]}/100", fg="#e67e22")
                    
                    # Convert frame for Tkinter display
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((280, 200))
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_lbl.imgtk = imgtk
                    video_lbl.configure(image=imgtk)
                    
                    # Repeat the loop
                    video_lbl.after(10, capture_loop)
            else:
                # --- When Capture Finishes (100 samples reached) ---
                if cap[0]: 
                    cap[0].release()
                is_capturing[0] = False
                video_lbl.pack_forget()
                
                # Now trigger the Trainer
                try:
                    progress_lbl.config(text="Retraining System... Please wait.", fg="#27ae60")
                    container.update() # Force UI refresh to show the message above
                    
                    # Call your training class
                    TrainImages(new_id=sid, training_type="student")
                    
                    progress_lbl.config(text="Update Complete ✅", fg="#27ae60")
                    messagebox.showinfo("Done", "Face samples captured and system retrained successfully!")
                except Exception as e:
                    messagebox.showerror("Trainer Error", f"Failed to retrain: {e}")

        # Start the loop
        capture_loop()

    def fetch_full_details():
        sid = id_ent.get()
        if not sid: return
        try:
            db = get_db_connection()
            cursor = db.cursor()
            query = """
                SELECT p.first_name, p.middle_name, p.last_name, p.email, p.phone, p.curr_address, p.perm_address,
                a.faculty, a.course, a.acad_year, a.guardian_name, a.guardian_phone, a.relationship, s.username
                FROM student_profiles p
                JOIN student_academic a ON p.student_id = a.student_id
                JOIN students s ON p.student_id = s.student_id
                WHERE p.student_id = %s
            """
            cursor.execute(query, (sid,))
            row = cursor.fetchone()
            db.close()
            if row:
                field_keys = ['fname', 'mname', 'lname', 'email', 'phone', 'curr_addr', 'perm_addr', 'faculty', 'course', 'year', 'p_name', 'p_phone', 'p_rel', 'user']
                for i, key in enumerate(field_keys):
                    val = str(row[i]) if row[i] else ""
                    if key in ['faculty', 'year', 'course']:
                        ents[key].set(val)
                        if key == 'faculty': update_courses()
                    else:
                        ents[key].delete(0, tk.END)
                        ents[key].insert(0, val)
            else:
                messagebox.showwarning("Warning", "ID not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Fetch failed: {e}")

    def save_data_only():
        sid = id_ent.get()
        if not sid: 
            messagebox.showerror("Error", "Please fetch a Student ID first.")
            return
        
        # 1. Clear previous errors
        for lbl in err_lbls.values(): lbl.config(text="")
        
        # 2. Prep and Validate data
        data = {k: v.get() for k, v in ents.items()}
        errors = Validator.validate_all(data)
        
        # During update, password can be empty
        if not data['pass'].strip() and 'pass' in errors:
            del errors['pass']

        if errors:
            for k, msg in errors.items():
                if k in err_lbls: err_lbls[k].config(text=f"⚠ {msg}")
            return

        # 3. Database Update ONLY
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("UPDATE student_profiles SET first_name=%s, middle_name=%s, last_name=%s, email=%s, phone=%s, curr_address=%s, perm_address=%s WHERE student_id=%s", 
                           (data['fname'], data['mname'], data['lname'], data['email'], data['phone'], data['curr_addr'], data['perm_addr'], sid))
            cursor.execute("UPDATE student_academic SET faculty=%s, course=%s, acad_year=%s, guardian_name=%s, guardian_phone=%s, relationship=%s WHERE student_id=%s", 
                           (data['faculty'], data['course'], data['year'], data['p_name'], data['p_phone'], data['p_rel'], sid))
            cursor.execute("UPDATE students SET username=%s WHERE student_id=%s", (data['user'], sid))
            
            if data['pass'].strip():
                cursor.execute("UPDATE students SET password=%s WHERE student_id=%s", (data['pass'], sid))
            
            db.commit()
            db.close()
            messagebox.showinfo("Success", "Database records updated! (System not retrained)")
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    # --- 3. UI BUILDING (Starts after functions are defined) ---
    header = tk.Frame(container, bg="#34495e", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="📑 STUDENT DATA & BIOMETRIC UPDATE", font=("Arial", 12, "bold"), bg="#34495e", fg="white").pack(pady=10)

    save_btn_frame = tk.Frame(container, bg="white", pady=10)
    save_btn_frame.pack(side="bottom", fill="x")

    search_row = tk.Frame(container, bg="#f4f7f6")
    search_row.pack(fill="x", padx=20, pady=10)
    tk.Label(search_row, text="Enter Student ID:", bg="#f4f7f6").pack(side="left")
    id_ent = tk.Entry(search_row, width=10, font=("Arial", 12))
    id_ent.pack(side="left", padx=10)
    tk.Button(search_row, text="🔍 Fetch Details", command=fetch_full_details, bg="#2980b9", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)

    main_body = tk.Frame(container, bg="white")
    main_body.pack(fill="both", expand=True, padx=20)

    # Sidebar (Right Column) - Pack this before Left Column
    right_col = tk.Frame(main_body, bg="#f4f7f6", width=300)
    right_col.pack(side="right", fill="y", padx=10)
    right_col.pack_propagate(False)

    tk.Label(right_col, text="BIOMETRIC & MEDIA", font=("Arial", 10, "bold"), bg="#f4f7f6", fg="#2c3e50").pack(pady=(20, 10))
    video_lbl = tk.Label(right_col, bg="black")
    progress_lbl = tk.Label(right_col, text="", bg="#f4f7f6")

    tk.Button(right_col, text="📸 Update Profile Picture", command=upload_profile_pic, bg="#3498db", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x", pady=5, padx=10)
    tk.Button(right_col, text="🧬 Update Face & Retrain", command=start_biometric_update,  bg="#e67e22", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x", pady=5, padx=10)

    # Form (Left Column)
    left_col = tk.Frame(main_body, bg="white")
    left_col.pack(side="left", fill="both", expand=True)
    canvas = tk.Canvas(left_col, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # 1. Define the scroll function
    def _on_mousewheel(event):
        # For Windows, we use event.delta
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # 2. Bind the event to the canvas and the frame
    # This ensures it scrolls even if your mouse is over a label or entry
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=400)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Helpers & Form Build
    def add_section(text):
        tk.Label(scrollable_frame, text=text.upper(), font=("Arial", 10, "bold"), bg="white", fg="#2c3e50").pack(anchor="w", pady=(15, 5))
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=2)

    def create_row(label_text, key, is_pass=False):
        tk.Label(scrollable_frame, text=label_text, bg="white", font=("Arial", 9)).pack(anchor="w", padx=5)
        ent = tk.Entry(scrollable_frame, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "")
        ent.pack(fill="x", padx=5, pady=(2, 0))
        err_msg = tk.Label(scrollable_frame, text="", font=("Arial", 8), fg="#e74c3c", bg="white")
        err_msg.pack(anchor="w", padx=5, pady=(0, 5))
        err_lbls[key] = err_msg
        return ent

    def update_courses(*args):
        courses = faculty_map.get(fac_var.get(), [])
        course_dropdown['values'] = courses
        if courses: course_dropdown.set(courses[0])

    # Add sections and fields here (omitted for brevity, same as previous version)
    add_section("1. Personal Information")
    ents['fname'] = create_row("First Name:", "fname")
    ents['mname'] = create_row("Middle Name (Optional):", "mname")
    ents['lname'] = create_row("Last Name:", "lname")

    add_section("2. Contact Information")
    ents['curr_addr'] = create_row("Current Address:", "curr_addr")
    ents['perm_addr'] = create_row("Permanent Address:", "perm_addr")
    ents['phone'] = create_row("Mobile Number:", "phone")
    ents['email'] = create_row("Email Address:", "email")

    add_section("3. Academic Details")
    tk.Label(scrollable_frame, text="Academic Year:", bg="white", font=("Arial", 9)).pack(anchor="w", padx=5)
    year_var = tk.StringVar(); year_dropdown = ttk.Combobox(scrollable_frame, textvariable=year_var, values=[str(y) for y in range(2024, 2031)], state="readonly")
    year_dropdown.pack(fill="x", padx=5, pady=5); ents['year'] = year_var

    tk.Label(scrollable_frame, text="Faculty:", bg="white", font=("Arial", 9)).pack(anchor="w", padx=5)
    fac_var = tk.StringVar(); ents['faculty'] = fac_var
    for fac in faculty_map.keys(): tk.Radiobutton(scrollable_frame, text=fac, variable=fac_var, value=fac, bg="white", command=update_courses).pack(anchor="w", padx=10)

    tk.Label(scrollable_frame, text="Course:", bg="white", font=("Arial", 9)).pack(anchor="w", padx=5)
    course_var = tk.StringVar(); course_dropdown = ttk.Combobox(scrollable_frame, textvariable=course_var, state="readonly")
    course_dropdown.pack(fill="x", padx=5, pady=5); ents['course'] = course_var

    add_section("4. Emergency Contact")
    ents['p_name'] = create_row("Guardian Name:", "p_name")
    ents['p_phone'] = create_row("Guardian Phone:", "p_phone")
    ents['p_rel'] = create_row("Relationship:", "p_rel")

    add_section("5. Account & Security")
    ents['user'] = create_row("Username:", "user")
    ents['pass'] = create_row("Password (Leave blank to keep current):", "pass", is_pass=True)

    tk.Button(save_btn_frame, text="💾 UPDATE DATABASE RECORDS", command=save_data_only, # Points to the new function
              bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", padx=100)