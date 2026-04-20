"""
edit_admin.py
─────────────
Admin profile editor — used by both:
  • Every admin editing their OWN profile  (allow_role_change=False)
  • Super Admins editing OTHER admins       (allow_role_change=True, from manage_admins)

New in this version
───────────────────
  ① Retrain Face button  — DB-first → then capture → then train → then notify
  ② Correct image paths:
       TrainingImage/admin/{admin_id}/{admin_id}.{n}.jpg
  ③ os.path.join used everywhere
  ④ Role change control (Super only)
"""

import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import os, shutil, bcrypt, cv2

from db_config   import get_db_connection
from session     import user_session
from train_image import TrainImages

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR  = os.path.join(BASE_DIR, "Admin_Profiles")
TRAIN_DIR   = os.path.join(BASE_DIR, "TrainingImage", "admin")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TRAIN_DIR,  exist_ok=True)


def edit_admin(container, admin_id, on_back_callback, allow_role_change=False):
    """
    allow_role_change : True only when a Super Admin edits another admin
                        from the Manage Admins panel.
    """
    for w in container.winfo_children():
        w.destroy()

    # ── Scrollable canvas ──────────────────────────────────────────────
    canvas = tk.Canvas(container, bg="#f4f7f6", highlightthickness=0)
    vsb    = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    sf     = tk.Frame(canvas, bg="#f4f7f6")          # scrollable_frame

    sf.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    def _scroll(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    canvas.bind_all("<MouseWheel>", _scroll)
    canvas.create_window((0, 0), window=sf, anchor="nw", width=900)
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # ── Shared state ───────────────────────────────────────────────────
    pic_path_var    = tk.StringVar()
    role_var        = tk.StringVar(value="Teacher")
    ents            = {}
    is_capturing    = [False]
    cap             = [None]
    sample_count    = [0]
    face_detector   = cv2.CascadeClassifier(
        os.path.join(BASE_DIR, "haarcascade_default.xml"))

    # ── Header ─────────────────────────────────────────────────────────
    hdr = tk.Frame(sf, bg="#2980b9", height=62)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    tk.Label(hdr, text="⚙️  Edit Admin Profile",
             font=("Arial", 15, "bold"),
             bg="#2980b9", fg="white").pack(pady=16)

    # ── Body: left form | right biometric ─────────────────────────────
    body = tk.Frame(sf, bg="#f4f7f6")
    body.pack(fill="both", expand=True, padx=18, pady=10)

    left_col  = tk.Frame(body, bg="white")
    left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

    right_col = tk.Frame(body, bg="#f4f7f6", width=260)
    right_col.pack(side="right", fill="y")
    right_col.pack_propagate(False)

    # ── ── ── LEFT COLUMN — form ── ── ──
    frm = tk.LabelFrame(left_col, text="Update Information",
                        bg="white", font=("Arial", 10, "bold"),
                        padx=14, pady=10)
    frm.pack(fill="x", pady=(0, 8))

    def field(label, row, is_pass=False):
        tk.Label(frm, text=label, bg="white",
                 font=("Arial", 9), width=32, anchor="w"
                 ).grid(row=row, column=0, sticky="w", pady=5)
        ent = tk.Entry(frm, font=("Arial", 10), bg="#f0f2f5",
                       show="*" if is_pass else "", width=38,
                       relief="flat",
                       highlightthickness=1, highlightbackground="#ccc")
        ent.grid(row=row, column=1, pady=5, padx=10)
        return ent

    ents["user"]  = field("Username:", 0)
    ents["pass"]  = field("New Password (blank = keep current):", 1, is_pass=True)
    ents["fname"] = field("First Name:", 2)
    ents["lname"] = field("Last Name:", 3)
    ents["phone"] = field("Phone No:", 4)
    ents["email"] = field("Email:", 5)

    tk.Label(frm, text="Date of Birth:", bg="white",
             font=("Arial", 9), anchor="w"
             ).grid(row=6, column=0, sticky="w", pady=5)
    ents["dob"] = DateEntry(frm, width=36, background="#2980b9", foreground="white")
    ents["dob"].grid(row=6, column=1, pady=5, padx=10)

    tk.Label(frm, text="Address:", bg="white",
             font=("Arial", 9), anchor="w"
             ).grid(row=7, column=0, sticky="nw", pady=5)
    ents["addr"] = tk.Text(frm, height=3, width=30,
                            font=("Arial", 10), bg="#f0f2f5", relief="flat",
                            highlightthickness=1, highlightbackground="#ccc")
    ents["addr"].grid(row=7, column=1, pady=5, padx=10)

    # Role selector (Super editing others only)
    if allow_role_change and user_session.is_super:
        role_frm = tk.LabelFrame(left_col, text="Admin Role",
                                  bg="white", font=("Arial", 10, "bold"),
                                  padx=14, pady=8)
        role_frm.pack(fill="x", pady=(0, 8))
        for r, c in [("Super", "#00d084"), ("Teacher", "#3498db")]:
            tk.Radiobutton(
                role_frm, text=f"  {r} Admin",
                variable=role_var, value=r,
                bg="white", font=("Arial", 10, "bold"),
                fg=c, activebackground="white", selectcolor="#f0f2f5"
            ).pack(side="left", padx=20, pady=4)

    # ── ── ── RIGHT COLUMN — photo + face retrain ── ── ──
    tk.Label(right_col, text="Profile Photo",
             font=("Arial", 10, "bold"), bg="#f4f7f6", fg="#555"
             ).pack(pady=(14, 4))

    preview_lbl = tk.Label(right_col, text="No Photo",
                            bg="#dde3ed", width=22, height=9,
                            font=("Arial", 9), fg="#888")
    preview_lbl.pack(padx=10)

    def upload_photo():
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not path:
            return
        uname = ents["user"].get().strip() or f"admin_{admin_id}"
        dest  = os.path.join(UPLOAD_DIR,
                             f"{uname}_profile{os.path.splitext(path)[1]}")
        shutil.copy(path, dest)
        img   = Image.open(dest).resize((160, 120), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(img)
        preview_lbl.configure(image=imgtk, text="")
        preview_lbl.image = imgtk
        pic_path_var.set(dest.replace("\\", "/"))

    tk.Button(right_col, text="📁  Upload Profile Photo",
              command=upload_photo,
              bg="#34495e", fg="white", relief="flat",
              pady=7, cursor="hand2").pack(fill="x", padx=10, pady=(6, 10))

    tk.Frame(right_col, bg="#ddd", height=1).pack(fill="x", padx=10, pady=4)

    tk.Label(right_col, text="Face Retraining",
             font=("Arial", 10, "bold"), bg="#f4f7f6", fg="#555"
             ).pack(pady=(8, 2))
    tk.Label(right_col,
             text="100 face samples will be captured\nand model retrained.",
             font=("Arial", 8), bg="#f4f7f6", fg="#999", justify="center"
             ).pack(padx=10)

    # Camera feed (hidden until capture starts)
    video_lbl    = tk.Label(right_col, bg="black")
    progress_lbl = tk.Label(right_col, text="",
                             font=("Arial", 9, "bold"),
                             bg="#f4f7f6", fg="#e67e22")

    def _stop_camera():
        is_capturing[0] = False
        if cap[0]:
            cap[0].release()
            cap[0] = None
        video_lbl.pack_forget()
        video_lbl.configure(image="")
        progress_lbl.pack_forget()

    def start_retrain():
        """
        Workflow:
          1. DB update (save current form data) FIRST
          2. Only if DB succeeds → start camera capture
          3. After 100 samples → TrainImages()
          4. Show success only after all steps done
        """
        # Step 1 — save to DB first
        if not _save_to_db(silent=True):
            messagebox.showerror(
                "Error",
                "Profile must be saved successfully before retraining.\n"
                "Please fix any errors and try again.")
            return

        # Step 2 — set up image folder
        train_folder = os.path.join(TRAIN_DIR, str(admin_id))
        os.makedirs(train_folder, exist_ok=True)

        video_lbl.configure(height=14, bg="black")
        video_lbl.pack(pady=(8, 2), padx=10, fill="x")
        progress_lbl.config(text="Starting camera…", fg="#e67e22")
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
                        fname = os.path.join(
                            train_folder,
                            f"{admin_id}.{sample_count[0]}.jpg")
                        cv2.imwrite(fname, gray[y:y+h, x:x+w])
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 208, 132), 2)

                    n = sample_count[0]
                    bar = "█" * (n // 10) + "░" * (10 - n // 10)
                    progress_lbl.config(
                        text=f"Capturing: {n}/100  [{bar}]", fg="#e67e22")

                    img   = Image.fromarray(
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).resize((220, 160))
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_lbl.imgtk = imgtk
                    video_lbl.configure(image=imgtk)

                container.after(10, capture_loop)
            else:
                # Step 3 — release camera, run training
                _stop_camera()
                progress_lbl.config(text="🔄  Training model…", fg="#3498db")
                progress_lbl.pack(pady=(4, 6))
                container.update()

                try:
                    success = TrainImages(new_id=admin_id, training_type="admin")
                    if success:
                        progress_lbl.config(text="✅  Retrain complete!", fg="#27ae60")
                        # Step 4 — notify only after both DB + training done
                        messagebox.showinfo(
                            "Retrain Complete",
                            "✅  Profile saved and face model retrained successfully!")
                    else:
                        messagebox.showerror(
                            "Training Failed",
                            "No face samples were captured.\nMake sure your face is visible.")
                except Exception as e:
                    messagebox.showerror("Training Error", f"Failed to retrain:\n{e}")

        capture_loop()

    tk.Button(right_col, text="🧬  Retrain Face",
              command=start_retrain,
              bg="#e67e22", fg="white",
              font=("Arial", 10, "bold"), relief="flat",
              pady=8, cursor="hand2").pack(fill="x", padx=10, pady=(8, 4))

    tk.Button(right_col, text="⏹  Stop Camera",
              command=_stop_camera,
              bg="#7f8c8d", fg="white",
              font=("Arial", 9), relief="flat",
              pady=6, cursor="hand2").pack(fill="x", padx=10)

    # ── Save logic ─────────────────────────────────────────────────────
    def _save_to_db(silent=False):
        """
        Persist form data. Returns True on success, False on failure.
        silent=True suppresses the success popup (used by retrain flow).
        """
        fname_val = ents["fname"].get().strip()
        lname_val = ents["lname"].get().strip()
        user_val  = ents["user"].get().strip()

        if not fname_val or not lname_val or not user_val:
            if not silent:
                messagebox.showwarning(
                    "Validation", "First name, last name, and username are required.")
            return False

        try:
            db     = get_db_connection()
            cursor = db.cursor()

            # username + optional password
            cursor.execute(
                "UPDATE admins SET username=%s WHERE admin_id=%s",
                (user_val, admin_id))

            new_pw = ents["pass"].get()
            if new_pw:
                hashed = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE admins SET password=%s WHERE admin_id=%s",
                    (hashed, admin_id))

            # role (only when a Super is editing another admin)
            if allow_role_change and user_session.is_super:
                cursor.execute(
                    "UPDATE admins SET role=%s WHERE admin_id=%s",
                    (role_var.get(), admin_id))

            # details row
            pic_val = pic_path_var.get()
            cursor.execute("""
                UPDATE admin_details
                SET first_name=%s,
                    last_name=%s,
                    dob=%s,
                    email=%s,
                    address=%s,
                    phone_no=%s,
                    profile_pic_path = COALESCE(NULLIF(%s,''), profile_pic_path)
                WHERE admin_id=%s
            """, (fname_val,
                  lname_val,
                  ents["dob"].get_date(),
                  ents["email"].get().strip(),
                  ents["addr"].get("1.0", "end-1c").strip(),
                  ents["phone"].get().strip(),
                  pic_val,
                  admin_id))

            db.commit()
            db.close()

            if not silent:
                messagebox.showinfo("Saved", "Profile updated successfully! ✅")
                on_back_callback()

            return True

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not save profile:\n{e}")
            return False

    # ── Footer ─────────────────────────────────────────────────────────
    footer = tk.Frame(sf, bg="#f4f7f6")
    footer.pack(fill="x", pady=16)

    tk.Button(footer, text="⬅  Cancel",
              command=on_back_callback,
              bg="#95a5a6", fg="white", relief="flat",
              width=14, pady=8, cursor="hand2"
              ).pack(side="left", padx=40)

    tk.Button(footer, text="💾  Save Changes",
              command=lambda: _save_to_db(silent=False),
              bg="#27ae60", fg="white",
              font=("Arial", 11, "bold"), relief="flat",
              width=24, pady=8, cursor="hand2"
              ).pack(side="right", padx=40)

    # ── Pre-fill form from DB ──────────────────────────────────────────
    def _load():
        try:
            db     = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""
                SELECT a.username, a.role,
                       d.first_name, d.last_name, d.dob,
                       d.email, d.address, d.phone_no, d.profile_pic_path
                FROM admins a
                JOIN admin_details d ON a.admin_id = d.admin_id
                WHERE a.admin_id = %s
            """, (admin_id,))
            row = cursor.fetchone()
            db.close()

            if not row:
                return

            ents["user"].insert(0, row["username"]   or "")
            ents["fname"].insert(0, row["first_name"] or "")
            ents["lname"].insert(0, row["last_name"]  or "")
            ents["phone"].insert(0, row["phone_no"]   or "")
            ents["email"].insert(0, row["email"]      or "")
            if row["dob"]:
                ents["dob"].set_date(row["dob"])
            ents["addr"].insert("1.0", row["address"] or "")
            role_var.set(row["role"] or "Teacher")

            pic = row["profile_pic_path"]
            if pic and os.path.exists(pic):
                img   = Image.open(pic).resize((160, 120), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(img)
                preview_lbl.configure(image=imgtk, text="")
                preview_lbl.image = imgtk
                pic_path_var.set(pic)

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load profile:\n{e}")

    _load()
