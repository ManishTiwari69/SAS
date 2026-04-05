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
    current_student_id = tk.StringVar() 
    current_status = tk.StringVar(value="Active")
    faculty_map = {
        "Management": ["BBA", "BBM", "BHM", "BTTM", "BIM"],
        "Humanities & Social Sciences": ["BA", "MA in Sociology", "Economics", "BCA"],
        "Law": ["LL.B.", "B.A.LL.B.", "LL.M."]
    }

    # --- 2. INTERNAL FUNCTIONS ---

    def upload_profile_pic():
        sid = current_student_id.get() # FIXED: Use StringVar
        username = ents['user'].get().strip()
        if not sid or not username:
            messagebox.showerror("Error", "Please fetch a student first!")
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
        sid = current_student_id.get() # FIXED: Use StringVar
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
                    faces = face_detector.detectMultiScale(gray, 1.3, 5)
                    
                    for (x, y, w, h) in faces:
                        sample_count[0] += 1
                        if not os.path.exists(student_folder): 
                            os.makedirs(student_folder)
                        
                        file_path = os.path.join(student_folder, f"{sid}.{sample_count[0]}.jpg")
                        cv2.imwrite(file_path, gray[y:y+h, x:x+w])
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    progress_lbl.config(text=f"Capturing: {sample_count[0]}/100", fg="#e67e22")
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((280, 200))
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_lbl.imgtk = imgtk
                    video_lbl.configure(image=imgtk)
                    video_lbl.after(10, capture_loop)
            else:
                if cap[0]: cap[0].release()
                is_capturing[0] = False
                video_lbl.pack_forget()
                
                try:
                    progress_lbl.config(text="Retraining System... Please wait.", fg="#27ae60")
                    container.update()
                    TrainImages(new_id=sid, training_type="student")
                    progress_lbl.config(text="Update Complete ✅", fg="#27ae60")
                    messagebox.showinfo("Done", "Face samples captured and system retrained!")
                except Exception as e:
                    messagebox.showerror("Trainer Error", f"Failed to retrain: {e}")

        capture_loop()

    def fetch_by_username():
        username = user_search_ent.get().strip()
        if not username:
            messagebox.showwarning("Input Required", "Please enter a username to search.")
            return
            
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT s.student_id, s.status, s.username, p.*, a.*
                FROM students s
                JOIN student_profiles p ON s.student_id = p.student_id
                JOIN student_academic a ON s.student_id = a.student_id
                WHERE s.username = %s
            """
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            db.close()

            if row:
                current_student_id.set(row['student_id'])
                current_status.set(row['status'])
                
                # Update Toggle Button
                toggle_btn.config(
                    text="🔓 Activate Student" if row['status'] == "Deactive" else "🔒 Deactivate Student",
                    bg="#27ae60" if row['status'] == "Deactive" else "#f39c12"
                )

                field_keys = {
                    'fname': row['first_name'], 'mname': row['middle_name'], 'lname': row['last_name'],
                    'email': row['email'], 'phone': row['phone'], 'curr_addr': row['curr_address'],
                    'perm_addr': row['perm_address'], 'faculty': row['faculty'], 'course': row['course'],
                    'year': row['acad_year'], 'p_name': row['guardian_name'], 'p_phone': row['guardian_phone'],
                    'p_rel': row['relationship'], 'user': row['username']
                }
                
                for key, val in field_keys.items():
                    value = str(val) if val else ""
                    if key in ['faculty', 'year', 'course']:
                        ents[key].set(value)
                        if key == 'faculty': update_courses()
                    else:
                        ents[key].delete(0, tk.END)
                        ents[key].insert(0, value)
            else:
                messagebox.showerror("Error", "Username not found.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Fetch failed: {e}")

    def toggle_status():
        sid = current_student_id.get()
        if not sid:
            messagebox.showwarning("Selection Required", "Please fetch a student record first.")
            return
        
        # Determine the new status string based on current state
        # If currently 'Active', we want to set it to 'Deactive'
        new_status = "Deactive" if current_status.get() == "Active" else "Active"
        
        confirm = messagebox.askyesno("Confirm Status Change", f"Are you sure you want to set this student to {new_status}?")
        
        if confirm:
            try:
                db = get_db_connection()
                cursor = db.cursor()
                
                # Execute the update on the 'students' table
                query = "UPDATE students SET status = %s WHERE student_id = %s"
                cursor.execute(query, (new_status, sid))
                
                db.commit()
                db.close()
                
                # Update the local state variable so the UI knows the new status
                current_status.set(new_status)
                
                # Refresh the UI (this will update button colors and text via fetch_by_username)
                fetch_by_username()
                
                messagebox.showinfo("Success", f"Student account is now {new_status}.")
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to update status: {e}")

    def delete_student():
        sid = current_student_id.get()
        username = ents['user'].get()
        if not sid: return
        if messagebox.askretrycancel("DANGER", f"Permanently delete {username}?"):
            try:
                db = get_db_connection()
                cursor = db.cursor()
                for table in ["student_academic", "student_profiles", "attendance_logs", "students"]:
                    cursor.execute(f"DELETE FROM {table} WHERE student_id = %s", (sid,))
                db.commit()
                db.close()
                path = os.path.join("TrainingImage", "student", username)
                if os.path.exists(path): shutil.rmtree(path)
                messagebox.showinfo("Deleted", "Student removed.")
                update_student(container)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def save_data_only():
        sid = current_student_id.get()
        if not sid: 
            messagebox.showerror("Error", "Fetch a student first.")
            return
        
        data = {k: v.get() for k, v in ents.items()}
        errors = Validator.validate_all(data)
        if not data['pass'].strip() and 'pass' in errors: del errors['pass']

        if errors:
            for k, msg in errors.items():
                if k in err_lbls: err_lbls[k].config(text=f"⚠ {msg}")
            return

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
            messagebox.showinfo("Success", "Records updated!")
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    # --- 3. UI BUILDING ---
    save_btn_frame = tk.Frame(container, bg="white", pady=10)
    save_btn_frame.pack(side="bottom", fill="x")

    search_row = tk.Frame(container, bg="#f4f7f6", pady=10)
    search_row.pack(fill="x", padx=20)
    
    tk.Label(search_row, text="Username:", bg="#f4f7f6", font=("Arial", 10)).pack(side="left")
    user_search_ent = tk.Entry(search_row, width=15, font=("Arial", 12))
    user_search_ent.pack(side="left", padx=5)

    tk.Button(search_row, text="🔍 Fetch", command=fetch_by_username, bg="#2980b9", fg="white").pack(side="left", padx=5)

    # Status Toggle & Delete Buttons
    toggle_btn = tk.Button(search_row, text="🔒 Deactivate", command=toggle_status, bg="#f39c12", fg="white")
    toggle_btn.pack(side="left", padx=5)
    
    tk.Button(search_row, text="🗑️ Delete", command=delete_student, bg="#e74c3c", fg="white").pack(side="left", padx=5)

    tk.Label(search_row, text="ID:", bg="#f4f7f6").pack(side="left", padx=(10, 0))
    tk.Label(search_row, textvariable=current_student_id, bg="#f4f7f6", fg="#7f8c8d", font=("Arial", 10, "bold")).pack(side="left")

    main_body = tk.Frame(container, bg="white")
    main_body.pack(fill="both", expand=True, padx=20)

    # Sidebar
    right_col = tk.Frame(main_body, bg="#f4f7f6", width=250)
    right_col.pack(side="right", fill="y", padx=10)
    right_col.pack_propagate(False)
    
    video_lbl = tk.Label(right_col, bg="black")
    progress_lbl = tk.Label(right_col, text="", bg="#f4f7f6")
    tk.Button(right_col, text="📸 Profile Pic", command=upload_profile_pic, bg="#3498db", fg="white").pack(fill="x", pady=5)
    tk.Button(right_col, text="🧬 Retrain Face", command=start_biometric_update, bg="#e67e22", fg="white").pack(fill="x", pady=5)

    # Scrollable Form
    left_col = tk.Frame(main_body, bg="white")
    left_col.pack(side="left", fill="both", expand=True)
    canvas = tk.Canvas(left_col, bg="white")
    scrollbar = ttk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=450)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def update_courses(*args):
        courses = faculty_map.get(fac_var.get(), [])
        course_dropdown['values'] = courses
        if courses: course_dropdown.set(courses[0])

    def create_row(label_text, key, is_pass=False):
        tk.Label(scrollable_frame, text=label_text, bg="white").pack(anchor="w", padx=5)
        ent = tk.Entry(scrollable_frame, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "")
        ent.pack(fill="x", padx=5, pady=(2, 0))
        err_msg = tk.Label(scrollable_frame, text="", font=("Arial", 8), fg="#e74c3c", bg="white")
        err_msg.pack(anchor="w", padx=5, pady=(0, 5))
        err_lbls[key] = err_msg
        return ent

    # Form Content
    ents['fname'] = create_row("First Name:", "fname")
    ents['mname'] = create_row("Middle Name:", "mname")
    ents['lname'] = create_row("Last Name:", "lname")
    ents['curr_addr'] = create_row("Current Address:", "curr_addr")
    ents['perm_addr'] = create_row("Permanent Address:", "perm_addr")
    ents['phone'] = create_row("Phone:", "phone")
    ents['email'] = create_row("Email:", "email")
    
    tk.Label(scrollable_frame, text="Faculty:", bg="white").pack(anchor="w", padx=5)
    fac_var = tk.StringVar(); ents['faculty'] = fac_var
    for fac in faculty_map.keys():
        tk.Radiobutton(scrollable_frame, text=fac, variable=fac_var, value=fac, bg="white", command=update_courses).pack(anchor="w")

    course_var = tk.StringVar(); ents['course'] = course_var
    course_dropdown = ttk.Combobox(scrollable_frame, textvariable=course_var, state="readonly")
    course_dropdown.pack(fill="x", padx=5, pady=5)
    
    year_var = tk.StringVar(); ents['year'] = year_var
    ttk.Combobox(scrollable_frame, textvariable=year_var, values=[str(y) for y in range(2024, 2030)]).pack(fill="x")

    ents['p_name'] = create_row("Guardian:", "p_name")
    ents['p_phone'] = create_row("Guardian Phone:", "p_phone")
    ents['p_rel'] = create_row("Relationship:", "p_rel")
    ents['user'] = create_row("Username:", "user")
    ents['pass'] = create_row("Password (Blank to keep):", "pass", is_pass=True)

    tk.Button(save_btn_frame, text="💾 SAVE ALL CHANGES", command=save_data_only, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", padx=100)