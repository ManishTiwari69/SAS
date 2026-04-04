import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import cv2
import os
from PIL import Image, ImageTk
from db_config import get_db_connection
from train_image import TrainImages 
import shutil

def update_student(container):
    # 1. Clear previous content
    for widget in container.winfo_children():
        widget.destroy()

    # --- State Variables ---
    is_capturing = [False]
    cap = [None]
    sample_count = [0]
    face_detector = cv2.CascadeClassifier("haarcascade_default.xml")
    ents = {}

    # --- Header ---
    header = tk.Frame(container, bg="#34495e", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="📑 STUDENT DATA & BIOMETRIC UPDATE", font=("Arial", 12, "bold"), 
             bg="#34495e", fg="white").pack(pady=10)

    # --- Bottom Save Button (Static) ---
    save_btn_frame = tk.Frame(container, bg="white", pady=10)
    save_btn_frame.pack(side="bottom", fill="x")

    # --- Search Bar (Top) ---
    search_row = tk.Frame(container, bg="#f4f7f6")
    search_row.pack(fill="x", padx=20, pady=10)
    
    tk.Label(search_row, text="Enter Student ID:", bg="#f4f7f6").pack(side="left")
    id_ent = tk.Entry(search_row, width=10, font=("Arial", 12))
    id_ent.pack(side="left", padx=10)

    # --- Main Content Layout ---
    main_body = tk.Frame(container, bg="white")
    main_body.pack(fill="both", expand=True, padx=20)

    # LEFT COLUMN: Scrollable Form
    left_col = tk.Frame(main_body, bg="white")
    left_col.pack(side="left", fill="both", expand=True)

    canvas = tk.Canvas(left_col, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="white")
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=400)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Form Builder Functions ---
    def add_section(text):
        tk.Label(scrollable_frame, text=text.upper(), font=("Arial", 10, "bold"), 
                 bg="white", fg="#2c3e50").pack(anchor="w", pady=(15, 5))
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=2)

    def create_row(label_text, is_pass=False):
        tk.Label(scrollable_frame, text=label_text, bg="white", font=("Arial", 9)).pack(anchor="w", padx=5)
        show_char = "*" if is_pass else ""
        ent = tk.Entry(scrollable_frame, font=("Arial", 10), bg="#f0f2f5", show=show_char)
        ent.pack(fill="x", padx=5, pady=(2, 8))
        return ent

    # Build Form Fields
    add_section("1. Personal Information")
    ents['fname'], ents['mname'], ents['lname'] = create_row("First Name:"), create_row("Middle Name:"), create_row("Last Name:")
    add_section("2. Contact Information")
    ents['curr_addr'], ents['perm_addr'], ents['phone'], ents['email'] = create_row("Current Address:"), create_row("Permanent Address:"), create_row("Mobile Number:"), create_row("Email Address:")
    add_section("3. Academic Details")
    ents['year'], ents['faculty'], ents['course'] = create_row("Academic Year:"), create_row("Faculty:"), create_row("Course:")
    add_section("4. Emergency Contact")
    ents['p_name'], ents['p_phone'], ents['p_rel'] = create_row("Guardian Name:"), create_row("Guardian Phone:"), create_row("Relationship:")
    add_section("5. Account & Security")
    ents['user'], ents['pass'] = create_row("Set Username:"), create_row("Set Password:", is_pass=True)

    # RIGHT COLUMN: Sidebar for Media
    right_col = tk.Frame(main_body, bg="#f4f7f6", width=300)
    right_col.pack(side="right", fill="y", padx=10)
    right_col.pack_propagate(False)

    tk.Label(right_col, text="BIOMETRIC & MEDIA", font=("Arial", 10, "bold"), 
             bg="#f4f7f6", fg="#2c3e50").pack(pady=(20, 10))

    # Define Video Labels early so functions can access them
    video_lbl = tk.Label(right_col, bg="black")
    progress_lbl = tk.Label(right_col, text="", bg="#f4f7f6")

    # --- Internal Functions ---

    def start_biometric_update():
        sid = id_ent.get()
        username = ents['user'].get().strip() # Matches key 'user' from form
        
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
                messagebox.showinfo("Done", f"Samples saved in: {username}")

        capture_loop()

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
                keys = ['fname', 'mname', 'lname', 'email', 'phone', 'curr_addr', 'perm_addr',
                        'faculty', 'course', 'year', 'p_name', 'p_phone', 'p_rel', 'user']
                for i, key in enumerate(keys):
                    ents[key].delete(0, tk.END)
                    ents[key].insert(0, str(row[i]) if row[i] else "")
            else:
                messagebox.showwarning("Warning", "ID not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Fetch failed: {e}")

    def save_and_train():
        sid = id_ent.get()
        if not sid: return
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("UPDATE student_profiles SET first_name=%s, middle_name=%s, last_name=%s, email=%s, phone=%s, curr_address=%s, perm_address=%s WHERE student_id=%s", 
                           (ents['fname'].get(), ents['mname'].get(), ents['lname'].get(), ents['email'].get(), ents['phone'].get(), ents['curr_addr'].get(), ents['perm_addr'].get(), sid))
            cursor.execute("UPDATE student_academic SET faculty=%s, course=%s, acad_year=%s, guardian_name=%s, guardian_phone=%s, relationship=%s WHERE student_id=%s", 
                           (ents['faculty'].get(), ents['course'].get(), ents['year'].get(), ents['p_name'].get(), ents['p_phone'].get(), ents['p_rel'].get(), sid))
            cursor.execute("UPDATE students SET username=%s WHERE student_id=%s", (ents['user'].get(), sid))
            if ents['pass'].get().strip():
                cursor.execute("UPDATE students SET password=%s WHERE student_id=%s", (ents['pass'].get().strip(), sid))
            db.commit()
            db.close()
            TrainImages(new_id=sid, training_type="student")
            messagebox.showinfo("Success", "Records updated and system retrained!")
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    # --- UI Buttons ---
    tk.Button(search_row, text="🔍 Fetch Details", command=fetch_full_details, 
              bg="#2980b9", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)

    tk.Button(right_col, text="📸 Update Profile Picture", command=upload_profile_pic, 
              bg="#3498db", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x", pady=5, padx=10)

    tk.Button(right_col, text="🧬 Update Face Recognition", command=start_biometric_update, 
              bg="#e67e22", fg="white", font=("Arial", 9, "bold"), height=2).pack(fill="x", pady=5, padx=10)

    tk.Button(save_btn_frame, text="💾 SAVE ALL DATA & UPDATE SYSTEM", command=save_and_train, 
              bg="#27ae60", fg="white", font=("Arial", 12, "bold"), height=2).pack(fill="x", padx=100)