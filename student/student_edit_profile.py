import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from db_config import get_db_connection
import cv2
import shutil
import bcrypt
from PIL import Image, ImageTk
from train_image import TrainImages

PRIMARY_COLOR = "#00d084"
BG_COLOR      = "#f8f9fa"

FACULTY_MAP = {
    "Management":                   ["BBA", "BBM", "BHM", "BTTM", "BIM"],
    "Humanities & Social Sciences": ["BA", "MA in Sociology", "Economics", "BCA"],
    "Law":                          ["LL.B.", "B.A.LL.B.", "LL.M."],
}


def show_edit_profile(container, student_id):
    """Render the Edit Profile view into container."""

    # ── mutable state (closures instead of class attributes) ───────────
    ents      = {}       # key → tk.Entry  OR  tk.StringVar
    err_lbls  = {}       # key → tk.Label  (inline error messages)

    is_capturing  = [False]
    cap           = [None]
    sample_count  = [0]
    face_detector = cv2.CascadeClassifier(
        os.path.join(os.path.dirname(__file__), "..", "haarcascade_default.xml"))

    # ── outer wrapper ──────────────────────────────────────────────────
    outer = tk.Frame(container, bg=BG_COLOR)
    outer.pack(fill="both", expand=True)

    # Title bar
    title_bar = tk.Frame(outer, bg=BG_COLOR)
    title_bar.pack(fill="x", padx=30, pady=(18, 0))
    tk.Label(title_bar, text="⚙️  Edit My Profile",
             font=("Arial", 16, "bold"),
             bg=BG_COLOR, fg="#1a1c23").pack(side="left")

    # ── Save button pinned to bottom ───────────────────────────────────
    save_bar = tk.Frame(outer, bg="white", pady=10)
    save_bar.pack(side="bottom", fill="x")

    # ── Main body ──────────────────────────────────────────────────────
    body = tk.Frame(outer, bg="white")
    body.pack(fill="both", expand=True, padx=20, pady=10)

    # ── RIGHT sidebar — photo + face retrain ───────────────────────────
    right_col = tk.Frame(body, bg="#f4f7f6", width=260)
    right_col.pack(side="right", fill="y", padx=(10, 0))
    right_col.pack_propagate(False)

    tk.Label(right_col, text="Biometric & Photo",
             font=("Arial", 11, "bold"),
             bg="#f4f7f6", fg="#555").pack(pady=(20, 8))

    # Profile picture preview
    photo_lbl = tk.Label(right_col, bg="#dde3ed", width=20, height=8,
                         cursor="hand2", text="Click to upload\nprofile picture",
                         font=("Arial", 9), fg="#888")
    photo_lbl.pack(padx=20, pady=(0, 8))

    def upload_photo():
        username = ents["user"].get().strip()
        if not username:
            messagebox.showerror("Error", "Cannot resolve username. Save profile first.")
            return
        path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if not path:
            return
        folder = os.path.join("TrainingImage", "student", username)
        os.makedirs(folder, exist_ok=True)
        ext  = os.path.splitext(path)[1]
        dest = os.path.join(folder, f"profile_{student_id}{ext}")
        shutil.copy(path, dest)
        img   = Image.open(dest).resize((160, 120))
        imgtk = ImageTk.PhotoImage(image=img)
        photo_lbl.imgtk = imgtk
        photo_lbl.configure(image=imgtk, text="")
        messagebox.showinfo("Success", "Profile photo updated!")

    photo_lbl.bind("<Button-1>", lambda e: upload_photo())

    tk.Button(right_col, text="📸  Upload Profile Photo",
              command=upload_photo,
              bg="#3498db", fg="white",
              font=("Arial", 10, "bold"), bd=0,
              pady=8, cursor="hand2").pack(fill="x", padx=20, pady=(0, 10))

    tk.Frame(right_col, bg="#ddd", height=1).pack(fill="x", padx=20, pady=8)

    tk.Label(right_col, text="Retrain Face ID",
             font=("Arial", 11, "bold"),
             bg="#f4f7f6", fg="#555").pack(pady=(4, 4))

    tk.Label(right_col,
             text="Point your face at the camera.\n100 samples will be captured\nand the model retrained.",
             font=("Arial", 9), bg="#f4f7f6", fg="#888", justify="center").pack(padx=16)

    video_lbl    = tk.Label(right_col, bg="black")
    progress_lbl = tk.Label(right_col, text="",
                             bg="#f4f7f6", fg="#e67e22",
                             font=("Arial", 10, "bold"))

    def stop_camera():
        is_capturing[0] = False
        if cap[0]:
            cap[0].release()
            cap[0] = None
        video_lbl.pack_forget()
        video_lbl.configure(image="")

    def start_face_retrain():
        username = ents["user"].get().strip()
        if not username:
            messagebox.showerror("Error", "Please save your profile before retraining.")
            return

        student_folder = os.path.join("TrainingImage", "student", username)
        os.makedirs(student_folder, exist_ok=True)

        video_lbl.configure(height=15, bg="black")
        video_lbl.pack(pady=(10, 2), padx=20, fill="x")
        progress_lbl.config(text="Starting camera…")
        progress_lbl.pack(pady=(0, 6))

        is_capturing[0]  = True
        sample_count[0]  = 0
        cap[0]           = cv2.VideoCapture(0)

        def capture_loop():
            if is_capturing[0] and sample_count[0] < 100:
                ret, frame = cap[0].read()
                if ret:
                    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_detector.detectMultiScale(gray, 1.3, 5)
                    for (x, y, w, h) in faces:
                        sample_count[0] += 1
                        save_path = os.path.join(
                            student_folder,
                            f"{student_id}.{sample_count[0]}.jpg")
                        cv2.imwrite(save_path, gray[y:y+h, x:x+w])
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                    count = sample_count[0]
                    progress_lbl.config(
                        text=f"Capturing: {count}/100  {'█' * (count // 10)}",
                        fg="#e67e22")

                    img   = Image.fromarray(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((220, 165))
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_lbl.imgtk = imgtk
                    video_lbl.configure(image=imgtk)

                container.after(10, capture_loop)
            else:
                stop_camera()
                try:
                    progress_lbl.config(text="🔄 Retraining model… please wait.", fg="#3498db")
                    container.update()
                    TrainImages(new_id=student_id, training_type="student")
                    progress_lbl.config(text="✅ Face retrain complete!", fg="#27ae60")
                    messagebox.showinfo("Done",
                                       "100 face samples captured.\n"
                                       "Face recognition model retrained successfully!")
                except Exception as e:
                    messagebox.showerror("Trainer Error", f"Retraining failed:\n{e}")

        capture_loop()

    tk.Button(right_col, text="🧬  Start Face Retrain",
              command=start_face_retrain,
              bg="#e67e22", fg="white",
              font=("Arial", 10, "bold"), bd=0,
              pady=8, cursor="hand2").pack(fill="x", padx=20, pady=10)

    tk.Button(right_col, text="⏹  Stop Camera",
              command=stop_camera,
              bg="#7f8c8d", fg="white",
              font=("Arial", 10), bd=0,
              pady=6, cursor="hand2").pack(fill="x", padx=20)

    # ── LEFT — scrollable form ─────────────────────────────────────────
    left_col = tk.Frame(body, bg="white")
    left_col.pack(side="left", fill="both", expand=True)

    canvas    = tk.Canvas(left_col, bg="white", highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
    sf        = tk.Frame(canvas, bg="white")   # sf = scrollable_frame

    sf.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=sf, anchor="nw", width=530)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    # ── form helpers ───────────────────────────────────────────────────
    def section(title):
        tk.Label(sf, text=title, font=("Arial", 11, "bold"),
                 bg="#eaf0fb", fg="#2c3e50",
                 anchor="w", padx=10).pack(fill="x", pady=(14, 4))

    def row(label, key, is_pass=False):
        tk.Label(sf, text=label, bg="white",
                 font=("Arial", 10), fg="#555").pack(anchor="w", padx=10)
        ent = tk.Entry(sf, font=("Arial", 11), bg="#f0f2f5", relief="flat",
                       highlightthickness=1, highlightbackground="#ccc",
                       show="*" if is_pass else "")
        ent.pack(fill="x", padx=10, pady=(2, 0), ipady=6)
        err = tk.Label(sf, text="", font=("Arial", 8), fg="#e74c3c", bg="white")
        err.pack(anchor="w", padx=10, pady=(0, 4))
        ents[key]     = ent
        err_lbls[key] = err

    # ── build form sections ────────────────────────────────────────────
    section("👤  Personal Information")
    row("First Name *",      "fname")
    row("Middle Name",       "mname")
    row("Last Name *",       "lname")
    row("Email *",           "email")
    row("Phone *",           "phone")
    row("Current Address",   "curr_addr")
    row("Permanent Address", "perm_addr")

    section("🎓  Academic Information")

    tk.Label(sf, text="Faculty *", bg="white",
             font=("Arial", 10), fg="#555").pack(anchor="w", padx=10)
    fac_var = tk.StringVar()
    ents["faculty"] = fac_var

    course_var = tk.StringVar()
    ents["course"] = course_var
    course_dd  = None   # forward reference; created after radio buttons

    def update_courses(*_):
        courses = FACULTY_MAP.get(fac_var.get(), [])
        course_dd["values"] = courses
        if courses:
            course_var.set(courses[0])

    for fac in FACULTY_MAP:
        tk.Radiobutton(sf, text=fac, variable=fac_var, value=fac,
                       bg="white", command=update_courses).pack(anchor="w", padx=20)

    tk.Label(sf, text="Course *", bg="white",
             font=("Arial", 10), fg="#555").pack(anchor="w", padx=10, pady=(6, 0))
    course_dd = ttk.Combobox(sf, textvariable=course_var,
                              state="readonly", font=("Arial", 11))
    course_dd.pack(fill="x", padx=10, pady=(2, 6), ipady=4)

    tk.Label(sf, text="Academic Year *", bg="white",
             font=("Arial", 10), fg="#555").pack(anchor="w", padx=10)
    year_var = tk.StringVar()
    ents["year"] = year_var
    ttk.Combobox(sf, textvariable=year_var,
                 values=[str(y) for y in range(2020, 2032)],
                 state="readonly", font=("Arial", 11)
                 ).pack(fill="x", padx=10, pady=(2, 6), ipady=4)

    section("👨‍👩‍👦  Guardian Information")
    row("Guardian Name",  "p_name")
    row("Guardian Phone", "p_phone")
    row("Relationship",   "p_rel")

    section("🔐  Account Settings")
    row("Username *",                   "user")
    row("New Password (blank = keep)",  "pass", is_pass=True)

    # ── pre-fill from DB ───────────────────────────────────────────────
    _load_data(student_id, ents, fac_var, course_var, year_var,
               update_courses, photo_lbl)

    # ── save handler ───────────────────────────────────────────────────
    def save():
        def v(key):
            obj = ents[key]
            return obj.get().strip() if hasattr(obj, "get") else ""

        fname    = v("fname");   lname    = v("lname")
        email    = v("email");   phone    = v("phone")
        mname    = v("mname");   curr     = v("curr_addr")
        perm     = v("perm_addr")
        faculty  = fac_var.get();  course = course_var.get()
        year     = year_var.get()
        p_name   = v("p_name");  p_phone = v("p_phone");  p_rel = v("p_rel")
        username = v("user");    password = v("pass")

        # Validation
        errors = {}
        if not fname:    errors["fname"] = "First name is required"
        if not lname:    errors["lname"] = "Last name is required"
        if not email:    errors["email"] = "Email is required"
        if not phone:    errors["phone"] = "Phone is required"
        if not username: errors["user"]  = "Username is required"

        for k, msg in errors.items():
            err_lbls[k].config(text=f"⚠ {msg}")
        for k in err_lbls:
            if k not in errors:
                err_lbls[k].config(text="")

        if errors:
            return

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                UPDATE student_profiles
                SET first_name=%s, middle_name=%s, last_name=%s,
                    email=%s, phone=%s, curr_address=%s, perm_address=%s
                WHERE student_id=%s
            """, (fname, mname, lname, email, phone, curr, perm, student_id))

            cursor.execute("""
                UPDATE student_academic
                SET faculty=%s, course=%s, acad_year=%s,
                    guardian_name=%s, guardian_phone=%s, relationship=%s
                WHERE student_id=%s
            """, (faculty, course, year, p_name, p_phone, p_rel, student_id))

            cursor.execute("UPDATE students SET username=%s WHERE student_id=%s",
                           (username, student_id))

            if password:
                hashed = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cursor.execute("UPDATE students SET password=%s WHERE student_id=%s",
                               (hashed, student_id))

            db.commit()
            db.close()
            messagebox.showinfo("Success", "Profile updated successfully! ✅")

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not save changes:\n{e}")

    # Wire save button now that save() is defined
    tk.Button(save_bar, text="💾  SAVE ALL CHANGES",
              command=save,
              bg=PRIMARY_COLOR, fg="white",
              font=("Arial", 12, "bold"), height=2, cursor="hand2"
              ).pack(fill="x", padx=120)


# ── DB loader (module-level helper) ───────────────────────────────────────

def _load_data(student_id, ents, fac_var, course_var, year_var,
               update_courses, photo_lbl):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.username,
                   p.first_name, p.middle_name, p.last_name,
                   p.email, p.phone, p.curr_address, p.perm_address,
                   a.faculty, a.course, a.acad_year,
                   a.guardian_name, a.guardian_phone, a.relationship
            FROM students s
            JOIN student_profiles p ON s.student_id = p.student_id
            JOIN student_academic  a ON s.student_id = a.student_id
            WHERE s.student_id = %s
        """, (student_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            messagebox.showerror("Error", "Profile not found.")
            return

        simple_map = {
            "fname":    row["first_name"],
            "mname":    row["middle_name"],
            "lname":    row["last_name"],
            "email":    row["email"],
            "phone":    row["phone"],
            "curr_addr":row["curr_address"],
            "perm_addr":row["perm_address"],
            "p_name":   row["guardian_name"],
            "p_phone":  row["guardian_phone"],
            "p_rel":    row["relationship"],
            "user":     row["username"],
        }
        for key, val in simple_map.items():
            ent = ents[key]
            ent.delete(0, tk.END)
            ent.insert(0, str(val) if val else "")

        # Dropdowns
        fac_var.set(row["faculty"] or "")
        update_courses()
        course_var.set(row["course"] or "")
        year_var.set(str(row["acad_year"]) if row["acad_year"] else "")

        # Profile photo preview
        username  = row["username"]
        photo_dir = os.path.join("TrainingImage", "student", username)
        for ext in (".jpg", ".jpeg", ".png"):
            pic = os.path.join(photo_dir, f"profile_{student_id}{ext}")
            if os.path.exists(pic):
                img   = Image.open(pic).resize((160, 120))
                imgtk = ImageTk.PhotoImage(image=img)
                photo_lbl.imgtk = imgtk
                photo_lbl.configure(image=imgtk, text="")
                break

    except Exception as e:
        messagebox.showerror("DB Error", f"Could not load profile:\n{e}")
