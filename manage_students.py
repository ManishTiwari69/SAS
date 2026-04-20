"""
manage_students.py
──────────────────
"Manage Students" view — accessible to BOTH Teacher and Super Admins.

Features
─────────
  • Searchable / filterable table of all students
  • Click a row → pre-fill edit form on the right
  • Save changes  (profile + academic + username/password)
  • Toggle Active / Deactive status
  • Delete student (with confirmation)
  • Retrain Face:
      1. DB update FIRST
      2. If DB succeeds → capture 100 face samples
      3. TrainImages() → StudentTrainner.yml
      4. Success notification only after both steps complete

Image storage:  TrainingImage/student/{student_id}/{student_id}.{n}.jpg
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import cv2, os, shutil, bcrypt
from PIL import Image, ImageTk

from db_config   import get_db_connection
from train_image import TrainImages
from validate    import Validator

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
TRAIN_DIR   = os.path.join(BASE_DIR, "TrainingImage", "student")
PROFILE_DIR = os.path.join(BASE_DIR, "Student_Profiles")
os.makedirs(TRAIN_DIR,   exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

FACULTY_MAP = {
    "Management":                   ["BBA", "BBM", "BHM", "BTTM", "BIM"],
    "Humanities & Social Sciences": ["BA", "MA in Sociology", "Economics", "BCA"],
    "Law":                          ["LL.B.", "B.A.LL.B.", "LL.M."],
}

# ── colours ────────────────────────────────────────────────────────────
PRIMARY = "#00d084"
BG      = "#f8f9fa"


def show_manage_students(container):
    """Entry-point called from main.py sidebar."""
    for w in container.winfo_children():
        w.destroy()

    # ── selected student state ─────────────────────────────────────────
    sel_id     = tk.StringVar()      # current student_id
    sel_status = tk.StringVar(value="Active")

    # ── layout: top search bar | left table | right edit panel ─────────
    top_bar = tk.Frame(container, bg=BG)
    top_bar.pack(fill="x", padx=20, pady=(16, 6))

    tk.Label(top_bar, text="👨‍🎓  Manage Students",
             font=("Arial", 17, "bold"), bg=BG, fg="#1a1c23"
             ).pack(side="left")

    # search widgets
    search_var = tk.StringVar()
    tk.Label(top_bar, text="Search:", bg=BG,
             font=("Arial", 10)).pack(side="right", padx=(0, 4))
    search_ent = tk.Entry(top_bar, textvariable=search_var,
                           font=("Arial", 11), width=22,
                           bg="white", relief="flat",
                           highlightthickness=1, highlightbackground="#ccc")
    search_ent.pack(side="right", padx=(0, 6), ipady=5)

    # ── main body ──────────────────────────────────────────────────────
    pane = tk.Frame(container, bg=BG)
    pane.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    # ── LEFT — student table ───────────────────────────────────────────
    table_frame = tk.Frame(pane, bg="white",
                            highlightthickness=1, highlightbackground="#ddd")
    table_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    style = ttk.Style()
    style.configure("Stu.Treeview",
                    background="white", foreground="#333",
                    rowheight=32, fieldbackground="white",
                    font=("Arial", 10))
    style.configure("Stu.Treeview.Heading",
                    font=("Arial", 10, "bold"), background="#f0f0f0")
    style.map("Stu.Treeview", background=[("selected", PRIMARY)])

    cols = ("ID", "Name", "Username", "Course", "Year", "Status")
    tree = ttk.Treeview(table_frame, columns=cols,
                        show="headings", style="Stu.Treeview",
                        selectmode="browse")

    col_w = {"ID": 45, "Name": 180, "Username": 120,
              "Course": 110, "Year": 60, "Status": 80}
    for c in cols:
        tree.heading(c, text=c,
                     command=lambda col=c: _sort_tree(tree, col))
        tree.column(c, anchor="center", width=col_w[c])

    tree.tag_configure("Active",   foreground="#27ae60")
    tree.tag_configure("Deactive", foreground="#e74c3c")

    vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # ── RIGHT — edit panel ─────────────────────────────────────────────
    right_panel = tk.Frame(pane, bg=BG, width=340)
    right_panel.pack(side="right", fill="y")
    right_panel.pack_propagate(False)

    _build_edit_panel(right_panel, sel_id, sel_status, tree, container)

    # ── wire up table selection → edit panel ──────────────────────────
    def _on_select(event):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0])["values"]
        sid  = vals[0]
        _load_student_into_panel(right_panel, sid, sel_id, sel_status,
                                  tree, container)

    tree.bind("<<TreeviewSelect>>", _on_select)

    # ── search / filter ────────────────────────────────────────────────
    all_rows = []   # cached from DB

    def _reload_table(filter_text=""):
        for row in tree.get_children():
            tree.delete(row)
        ft = filter_text.strip().lower()
        for r in all_rows:
            if ft and ft not in " ".join(str(v) for v in r).lower():
                continue
            status = r[5]
            tree.insert("", "end", values=r, tags=(status,))

    def _fetch_all():
        nonlocal all_rows
        try:
            db     = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT s.student_id,
                       CONCAT(p.first_name,' ',p.last_name),
                       s.username,
                       a.course, a.acad_year, s.status
                FROM students s
                JOIN student_profiles p  ON s.student_id = p.student_id
                JOIN student_academic a  ON s.student_id = a.student_id
                ORDER BY p.first_name, p.last_name
            """)
            all_rows = cursor.fetchall()
            db.close()
            _reload_table()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not fetch students:\n{e}")

    search_var.trace_add("write",
                         lambda *_: _reload_table(search_var.get()))

    tk.Button(top_bar, text="🔄  Refresh",
              command=_fetch_all,
              bg=PRIMARY, fg="white",
              font=("Arial", 9, "bold"), relief="flat",
              padx=12, pady=5, cursor="hand2"
              ).pack(side="right", padx=(0, 8))

    _fetch_all()


# ──────────────────────────────────────────────────────────────────────
#  EDIT PANEL
# ──────────────────────────────────────────────────────────────────────

def _build_edit_panel(panel, sel_id, sel_status, tree, container):
    """Build the persistent right-side edit panel (widgets only, no data)."""

    # placeholder shown before any row is selected
    tk.Label(panel,
             text="← Select a student\nfrom the table to edit",
             font=("Arial", 10), bg=BG, fg="#aaa",
             justify="center").pack(expand=True)


def _load_student_into_panel(panel, student_id, sel_id, sel_status,
                              tree, container):
    """Clear the panel and rebuild it with data for student_id."""
    for w in panel.winfo_children():
        w.destroy()

    sel_id.set(str(student_id))

    # ── scrollable canvas inside the right panel ───────────────────────
    rcanvas = tk.Canvas(panel, bg=BG, highlightthickness=0)
    rvsb    = tk.Scrollbar(panel, orient="vertical", command=rcanvas.yview)
    rsf     = tk.Frame(rcanvas, bg=BG)
    rsf.bind("<Configure>",
             lambda e: rcanvas.configure(scrollregion=rcanvas.bbox("all")))

    def _rscroll(event):
        try:
            if rcanvas.winfo_exists():
                rcanvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass

    rcanvas.bind_all("<MouseWheel>", _rscroll)
    rcanvas.create_window((0, 0), window=rsf, anchor="nw", width=330)
    rcanvas.configure(yscrollcommand=rvsb.set)
    rcanvas.pack(side="left", fill="both", expand=True)
    rvsb.pack(side="right", fill="y")

    # ── fetch student record ───────────────────────────────────────────
    try:
        db     = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.student_id, s.username, s.status,
                   p.first_name, p.middle_name, p.last_name,
                   p.email, p.phone, p.curr_address, p.perm_address,
                   a.faculty, a.course, a.acad_year,
                   a.guardian_name, a.guardian_phone, a.relationship
            FROM students s
            JOIN student_profiles p ON s.student_id = p.student_id
            JOIN student_academic a ON s.student_id = a.student_id
            WHERE s.student_id = %s
        """, (student_id,))
        row = cursor.fetchone()
        db.close()
    except Exception as e:
        messagebox.showerror("DB Error", str(e))
        return

    if not row:
        return

    sel_status.set(row["status"])

    # ── shared widget refs ─────────────────────────────────────────────
    ents     = {}
    err_lbls = {}

    # biometric state
    is_capturing  = [False]
    cap           = [None]
    sample_count  = [0]
    face_detector = cv2.CascadeClassifier(
        os.path.join(BASE_DIR, "haarcascade_default.xml"))

    # ── title + action buttons ─────────────────────────────────────────
    th = tk.Frame(rsf, bg="#1a1c23")
    th.pack(fill="x")
    tk.Label(th,
             text=f"✏️  {row['first_name']} {row['last_name']}",
             font=("Arial", 11, "bold"), bg="#1a1c23", fg="#00d084"
             ).pack(side="left", padx=12, pady=10)

    def _refresh_tree():
        """Reload the left table after a change."""
        # Re-fetch the single row and update it
        try:
            db     = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                SELECT s.student_id,
                       CONCAT(p.first_name,' ',p.last_name),
                       s.username, a.course, a.acad_year, s.status
                FROM students s
                JOIN student_profiles p ON s.student_id=p.student_id
                JOIN student_academic a ON s.student_id=a.student_id
                WHERE s.student_id=%s
            """, (student_id,))
            r = cursor.fetchone()
            db.close()
            if r:
                for item in tree.get_children():
                    if str(tree.item(item)["values"][0]) == str(student_id):
                        tree.item(item, values=r, tags=(r[5],))
                        break
        except Exception:
            pass

    # action buttons row
    ab = tk.Frame(rsf, bg=BG)
    ab.pack(fill="x", padx=6, pady=6)

    toggle_btn = tk.Button(
        ab,
        text="🔓 Activate" if row["status"] == "Deactive" else "🔒 Deactivate",
        bg="#27ae60" if row["status"] == "Deactive" else "#f39c12",
        fg="white", relief="flat", font=("Arial", 9, "bold"),
        padx=8, pady=5, cursor="hand2",
        command=lambda: _toggle_status(student_id, sel_status,
                                        toggle_btn, _refresh_tree))
    toggle_btn.pack(side="left", padx=(0, 6))

    tk.Button(ab, text="🗑️ Delete",
              bg="#e74c3c", fg="white", relief="flat",
              font=("Arial", 9, "bold"), padx=8, pady=5, cursor="hand2",
              command=lambda: _delete_student(
                  student_id, row["username"], tree, panel,
                  sel_id, sel_status, container)).pack(side="left")

    # ── section helper ─────────────────────────────────────────────────
    def section(text):
        tk.Label(rsf, text=text, font=("Arial", 9, "bold"),
                 bg="#eaf0fb", fg="#2c3e50", anchor="w", padx=8
                 ).pack(fill="x", pady=(10, 3))

    def row_field(label, key, is_pass=False):
        tk.Label(rsf, text=label, bg=BG,
                 font=("Arial", 9), fg="#555").pack(anchor="w", padx=8)
        ent = tk.Entry(rsf, font=("Arial", 10), bg="white", relief="flat",
                       highlightthickness=1, highlightbackground="#ccc",
                       show="*" if is_pass else "")
        ent.pack(fill="x", padx=8, pady=(2, 0), ipady=5)
        err = tk.Label(rsf, text="", font=("Arial", 8),
                       fg="#e74c3c", bg=BG)
        err.pack(anchor="w", padx=8, pady=(0, 3))
        ents[key]     = ent
        err_lbls[key] = err
        return ent

    # ── Personal ───────────────────────────────────────────────────────
    section("👤  Personal")
    row_field("First Name *",      "fname")
    row_field("Middle Name",       "mname")
    row_field("Last Name *",       "lname")
    row_field("Email *",           "email")
    row_field("Phone *",           "phone")
    row_field("Current Address",   "curr_addr")
    row_field("Permanent Address", "perm_addr")

    # ── Academic ───────────────────────────────────────────────────────
    section("🎓  Academic")

    tk.Label(rsf, text="Faculty *", bg=BG,
             font=("Arial", 9), fg="#555").pack(anchor="w", padx=8)
    fac_var = tk.StringVar(value=row["faculty"] or "Management")
    ents["faculty"] = fac_var

    course_var = tk.StringVar(value=row["course"] or "")
    ents["course"] = course_var
    course_dd  = [None]   # mutable reference

    def update_courses(*_):
        courses = FACULTY_MAP.get(fac_var.get(), [])
        if course_dd[0]:
            course_dd[0]["values"] = courses
            if not course_var.get() in courses and courses:
                course_var.set(courses[0])

    for fac in FACULTY_MAP:
        tk.Radiobutton(rsf, text=fac, variable=fac_var, value=fac,
                       bg=BG, font=("Arial", 9),
                       command=update_courses).pack(anchor="w", padx=20)

    tk.Label(rsf, text="Course *", bg=BG,
             font=("Arial", 9), fg="#555").pack(anchor="w", padx=8, pady=(4, 0))
    _dd = ttk.Combobox(rsf, textvariable=course_var,
                        state="readonly", font=("Arial", 10))
    _dd.pack(fill="x", padx=8, pady=(2, 4), ipady=3)
    course_dd[0] = _dd
    update_courses()

    tk.Label(rsf, text="Academic Year *", bg=BG,
             font=("Arial", 9), fg="#555").pack(anchor="w", padx=8)
    year_var = tk.StringVar(value=str(row["acad_year"]) if row["acad_year"] else "")
    ents["year"] = year_var
    ttk.Combobox(rsf, textvariable=year_var,
                 values=[str(y) for y in range(2020, 2032)],
                 state="readonly", font=("Arial", 10)
                 ).pack(fill="x", padx=8, pady=(2, 4), ipady=3)

    # ── Guardian ───────────────────────────────────────────────────────
    section("👨‍👩‍👦  Guardian")
    row_field("Guardian Name",  "p_name")
    row_field("Guardian Phone", "p_phone")
    row_field("Relationship",   "p_rel")

    # ── Account ────────────────────────────────────────────────────────
    section("🔐  Account")
    row_field("Username *",                   "user")
    row_field("New Password (blank = keep)",  "pass", is_pass=True)

    # ── Biometrics ─────────────────────────────────────────────────────
    section("🧬  Face Retraining")
    video_lbl    = tk.Label(rsf, bg="black")
    progress_lbl = tk.Label(rsf, text="",
                             font=("Arial", 9, "bold"), bg=BG, fg="#e67e22")

    def _stop_cam():
        is_capturing[0] = False
        if cap[0]:
            cap[0].release()
            cap[0] = None
        video_lbl.pack_forget()
        video_lbl.configure(image="")
        progress_lbl.pack_forget()

    def start_retrain():
        # Step 1 — DB save first
        if not _save_student(student_id, ents, fac_var, course_var,
                              year_var, err_lbls, silent=True):
            messagebox.showerror(
                "Error",
                "Please fix validation errors before retraining.")
            return

        train_folder = os.path.join(TRAIN_DIR, str(student_id))
        os.makedirs(train_folder, exist_ok=True)

        video_lbl.configure(height=10, bg="black")
        video_lbl.pack(padx=8, pady=(6, 2), fill="x")
        progress_lbl.config(text="Starting camera…", fg="#e67e22")
        progress_lbl.pack(padx=8, pady=(0, 4))

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
                        img_path = os.path.join(
                            train_folder,
                            f"{student_id}.{sample_count[0]}.jpg")
                        cv2.imwrite(img_path, gray[y:y+h, x:x+w])
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 208, 132), 2)

                    n   = sample_count[0]
                    bar = "█"*(n//10) + "░"*(10 - n//10)
                    progress_lbl.config(
                        text=f"Capturing {n}/100 [{bar}]", fg="#e67e22")

                    img   = Image.fromarray(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((300, 180))
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_lbl.imgtk = imgtk
                    video_lbl.configure(image=imgtk)

                container.after(10, capture_loop)
            else:
                _stop_cam()
                progress_lbl.config(text="🔄  Training…", fg="#3498db")
                progress_lbl.pack(padx=8, pady=(4, 4))
                container.update()
                try:
                    ok = TrainImages(new_id=student_id, training_type="student")
                    if ok:
                        progress_lbl.config(text="✅  Done!", fg="#27ae60")
                        messagebox.showinfo(
                            "Complete",
                            "✅  Profile saved and face model retrained!")
                    else:
                        messagebox.showerror(
                            "Training Failed",
                            "No face samples captured.\nMake sure your face is visible.")
                except Exception as e:
                    messagebox.showerror("Training Error", str(e))

        capture_loop()

    bio_row = tk.Frame(rsf, bg=BG)
    bio_row.pack(fill="x", padx=8, pady=4)

    tk.Button(bio_row, text="🧬  Retrain Face",
              command=start_retrain,
              bg="#e67e22", fg="white", relief="flat",
              font=("Arial", 9, "bold"), padx=10, pady=6, cursor="hand2"
              ).pack(side="left", padx=(0, 6))

    tk.Button(bio_row, text="⏹",
              command=_stop_cam,
              bg="#7f8c8d", fg="white", relief="flat",
              pady=6, cursor="hand2").pack(side="left")

    # ── Save row ───────────────────────────────────────────────────────
    tk.Button(rsf, text="💾  Save Changes",
              command=lambda: _save_student(
                  student_id, ents, fac_var, course_var, year_var,
                  err_lbls, silent=False,
                  on_success=_refresh_tree),
              bg=PRIMARY, fg="white",
              font=("Arial", 10, "bold"), relief="flat",
              pady=8, cursor="hand2"
              ).pack(fill="x", padx=8, pady=(10, 16))

    # ── Pre-fill entries ───────────────────────────────────────────────
    simple = {
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
    for k, v in simple.items():
        ents[k].insert(0, str(v) if v else "")

    fac_var.set(row["faculty"] or "Management")
    update_courses()
    course_var.set(row["course"] or "")
    year_var.set(str(row["acad_year"]) if row["acad_year"] else "")


# ──────────────────────────────────────────────────────────────────────
#  DB HELPERS
# ──────────────────────────────────────────────────────────────────────

def _save_student(student_id, ents, fac_var, course_var, year_var,
                  err_lbls, silent=False, on_success=None):
    """
    Persist form data to DB.
    Returns True on success, False on validation / DB error.
    silent=True suppresses the success popup (retrain flow).
    """
    def v(k):
        obj = ents.get(k)
        if obj is None: return ""
        return obj.get().strip() if hasattr(obj, "get") else ""

    fname    = v("fname"); lname  = v("lname")
    email    = v("email"); phone  = v("phone")
    mname    = v("mname")
    curr     = v("curr_addr"); perm = v("perm_addr")
    faculty  = fac_var.get();  course = course_var.get()
    year     = year_var.get()
    p_name   = v("p_name"); p_phone = v("p_phone"); p_rel = v("p_rel")
    username = v("user");   password = v("pass")

    # Validation
    errors = {}
    if not fname:    errors["fname"] = "Required"
    if not lname:    errors["lname"] = "Required"
    if not email:    errors["email"] = "Required"
    if not phone:    errors["phone"] = "Required"
    if not username: errors["user"]  = "Required"

    for k, msg in errors.items():
        if k in err_lbls:
            err_lbls[k].config(text=f"⚠ {msg}")
    for k in err_lbls:
        if k not in errors:
            err_lbls[k].config(text="")

    if errors:
        return False

    try:
        db     = get_db_connection()
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
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            cursor.execute("UPDATE students SET password=%s WHERE student_id=%s",
                           (hashed, student_id))

        db.commit()
        db.close()

        if not silent:
            messagebox.showinfo("Saved", "Student record updated ✅")
        if on_success:
            on_success()

        return True

    except Exception as e:
        messagebox.showerror("DB Error", f"Could not save:\n{e}")
        return False


def _toggle_status(student_id, sel_status, btn, on_done):
    current    = sel_status.get()
    new_status = "Active" if current == "Deactive" else "Deactive"

    if not messagebox.askyesno(
            "Confirm",
            f"Set student status to '{new_status}'?"):
        return

    try:
        db     = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE students SET status=%s WHERE student_id=%s",
                       (new_status, student_id))
        db.commit()
        db.close()

        sel_status.set(new_status)
        btn.config(
            text="🔓 Activate" if new_status == "Deactive" else "🔒 Deactivate",
            bg="#27ae60" if new_status == "Deactive" else "#f39c12")
        messagebox.showinfo("Updated", f"Status set to {new_status}.")
        on_done()

    except Exception as e:
        messagebox.showerror("DB Error", str(e))


def _delete_student(student_id, username, tree, panel,
                    sel_id, sel_status, container):
    if not messagebox.askyesno(
            "⚠️  Confirm Delete",
            f"Permanently delete student '{username}'?\n"
            "This cannot be undone."):
        return

    try:
        db     = get_db_connection()
        cursor = db.cursor()
        for tbl in ["student_academic", "student_profiles",
                    "attendance_logs", "students"]:
            cursor.execute(f"DELETE FROM {tbl} WHERE student_id=%s",
                           (student_id,))
        db.commit()
        db.close()

        # Remove training images
        train_folder = os.path.join(TRAIN_DIR, str(student_id))
        if os.path.exists(train_folder):
            shutil.rmtree(train_folder)

        # Remove row from tree
        for item in tree.get_children():
            if str(tree.item(item)["values"][0]) == str(student_id):
                tree.delete(item)
                break

        # Clear right panel
        for w in panel.winfo_children():
            w.destroy()
        sel_id.set("")
        tk.Label(panel,
                 text="← Select a student\nfrom the table to edit",
                 font=("Arial", 10), bg=BG, fg="#aaa",
                 justify="center").pack(expand=True)

        messagebox.showinfo("Deleted", f"Student '{username}' removed.")

    except Exception as e:
        messagebox.showerror("DB Error", str(e))


# ── tree column sort ───────────────────────────────────────────────────
_sort_state = {}

def _sort_tree(tree, col):
    data = [(tree.set(k, col), k) for k in tree.get_children("")]
    rev  = _sort_state.get(col, False)
    data.sort(reverse=rev)
    for i, (_, k) in enumerate(data):
        tree.move(k, "", i)
    _sort_state[col] = not rev
