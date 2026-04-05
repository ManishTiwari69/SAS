import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import cv2
import os
import re
import shutil
import bcrypt
from db_config import get_db_connection
from validate import AdminValidator

UPLOAD_DIR = "Admin_Profiles"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def register_admin(container):
    # 1. Clear everything
    for widget in container.winfo_children():
        widget.destroy()

    # 2. Setup Scrollable Infrastructure
    canvas = tk.Canvas(container, bg="#f4f7f6", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f4f7f6")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # 1. Define the scroll function
    def _on_mousewheel(event):
        # For Windows, we use event.delta
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # 2. Bind the event to the canvas and the frame
    # This ensures it scrolls even if your mouse is over a label or entry
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=container.winfo_width())
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Variables & State ---
    selected_pic_relative_path = tk.StringVar()
    gender_var = tk.StringVar(value="Male")
    is_capturing = [False] 
    cap = [None]
    ents = {}
    err_lbls = {}
    sample_count = [0]
    face_detector = cv2.CascadeClassifier("haarcascade_default.xml")

    # --- 3. Logic Functions (Defined before UI) ---
    def back_to_dash():
        if cap[0]: cap[0].release()
        root = container.winfo_toplevel()
        import main
        main.render_dashboard(root)

    def upload_image():
        abs_path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if abs_path:
            username = ents['user'].get() or "admin"
            filename = f"{username}_profile{os.path.splitext(abs_path)[1]}"
            dest_path = os.path.join(UPLOAD_DIR, filename)
            shutil.copy(abs_path, dest_path)

            img = Image.open(dest_path).resize((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            preview_lbl.config(image=photo, text="")
            preview_lbl.image = photo
            selected_pic_relative_path.set(dest_path.replace("\\", "/"))

    def update_capture_feed():
        if is_capturing[0] and sample_count[0] < 100:
            ret, frame = cap[0].read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    sample_count[0] += 1
                    if not os.path.exists("TrainingImage"): os.makedirs("TrainingImage")
                    cv2.imwrite(f"TrainingImage/{ents['user'].get()}.{sample_count[0]}.jpg", gray[y:y+h, x:x+w])
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((400, 300), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                video_lbl.imgtk = imgtk
                video_lbl.configure(image=imgtk)
                
                if sample_count[0] < 100:
                    container.after(10, update_capture_feed)
                else:
                    finish_registration()

    def start_process():
        for lbl in err_lbls.values(): lbl.config(text="")
        admin_data = {
            'user': ents['user'].get().strip(),
            'pass': ents['pass'].get(),
            'fname': ents['fname'].get().strip(),
            'lname': ents['lname'].get().strip(),
            'email': ents['email'].get().strip(),
            'phone': ents['phone'].get().strip(),
            'addr': ents['addr'].get("1.0", "end-1c").strip(),
            'pic_path': selected_pic_relative_path.get()
        }
        errors = AdminValidator.validate_admin(admin_data)
        if errors:
            for key, message in errors.items():
                if key in err_lbls: err_lbls[key].config(text=f"⚠ {message}")
            return

        is_capturing[0] = True
        cap[0] = cv2.VideoCapture(0)
        update_capture_feed()

    def finish_registration():
        is_capturing[0] = False
        if cap[0]: cap[0].release()
        try:
            db = get_db_connection()
            cursor = db.cursor()
            hashed = bcrypt.hashpw(ents['pass'].get().encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (ents['user'].get(), hashed))
            admin_id = cursor.lastrowid
            sql = "INSERT INTO admin_details (admin_id, first_name, last_name, dob, gender, email, address, phone_no, profile_pic_path) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (admin_id, ents['fname'].get(), ents['lname'].get(), ents['dob'].get_date(), gender_var.get(), ents['email'].get(), ents['addr'].get("1.0", "end-1c"), ents['phone'].get(), selected_pic_relative_path.get()))
            db.commit()
            db.close()
            messagebox.showinfo("Success", "Admin Registration Complete!")
            back_to_dash()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")

    # --- 4. Build UI (Strictly inside scrollable_frame) ---
    header = tk.Frame(scrollable_frame, bg="#3498db", height=60)
    header.pack(fill="x")
    tk.Label(header, text="🛡️ NEW ADMIN REGISTRATION", font=("Arial", 14, "bold"), bg="#3498db", fg="white").pack(pady=15)

    main_frame = tk.Frame(scrollable_frame, bg="#f4f7f6")
    main_frame.pack(fill="both", expand=True, padx=20, pady=5)

    # Left Column
    left_column = tk.Frame(main_frame, bg="#f4f7f6")
    left_column.pack(side="left", fill="both", expand=True, padx=5)

    form_frame = tk.LabelFrame(left_column, text="Admin Details", bg="white", font=("Arial", 10, "bold"), padx=15, pady=10)
    form_frame.pack(fill="x", pady=5)

    def create_field(label, row, key, is_pass=False):
        tk.Label(form_frame, text=label, bg="white", font=("Arial", 9)).grid(row=row*2, column=0, sticky="w")
        entry = tk.Entry(form_frame, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "", width=30)
        entry.grid(row=row*2, column=1, pady=(5, 0), padx=10)
        err_msg = tk.Label(form_frame, text="", font=("Arial", 8), fg="#e74c3c", bg="white", wraplength=200, justify="left")
        err_msg.grid(row=row*2 + 1, column=1, sticky="w", padx=10)
        err_lbls[key] = err_msg
        return entry

    ents['user'] = create_field("Username:", 0, 'user')
    ents['pass'] = create_field("Password:", 1, 'pass', is_pass=True)
    ents['fname'] = create_field("First Name:", 2, 'fname')
    ents['lname'] = create_field("Last Name:", 3, 'lname')
    ents['phone'] = create_field("Phone No:", 4, 'phone')

    # Email
    tk.Label(form_frame, text="Email:", bg="white", font=("Arial", 9)).grid(row=10, column=0, sticky="w")
    ents['email'] = tk.Entry(form_frame, font=("Arial", 10), bg="#f0f2f5", width=30)
    ents['email'].grid(row=10, column=1, pady=(5,0), padx=10)
    err_lbls['email'] = tk.Label(form_frame, text="", font=("Arial", 8), fg="#e74c3c", bg="white")
    err_lbls['email'].grid(row=11, column=1, sticky="w", padx=10)

    # DOB
    tk.Label(form_frame, text="DOB:", bg="white", font=("Arial", 9)).grid(row=12, column=0, sticky="w")
    ents['dob'] = DateEntry(form_frame, width=28, background='darkblue', foreground='white')
    ents['dob'].grid(row=12, column=1, pady=5, padx=10)

    # Address
    tk.Label(form_frame, text="Address:", bg="white", font=("Arial", 9)).grid(row=13, column=0, sticky="nw")
    ents['addr'] = tk.Text(form_frame, height=3, width=23, font=("Arial", 10), bg="#f0f2f5")
    ents['addr'].grid(row=13, column=1, pady=5, padx=10)
    err_lbls['addr'] = tk.Label(form_frame, text="", font=("Arial", 8), fg="#e74c3c", bg="white")
    err_lbls['addr'].grid(row=14, column=1, sticky="w", padx=10)

    preview_lbl = tk.Label(left_column, text="No Image", bg="#dfe6e9", width=20, height=10)
    preview_lbl.pack(pady=5)
    tk.Button(left_column, text="📁 Upload Photo", command=upload_image, bg="#34495e", fg="white").pack(fill="x")

    # Right Column
    right_column = tk.Frame(main_frame, bg="#f4f7f6")
    right_column.pack(side="right", fill="both", expand=True, padx=10)
    cam_box = tk.LabelFrame(right_column, text="Internal Face Capture", bg="white", font=("Arial", 10, "bold"))
    cam_box.pack(fill="both", expand=True)
    video_lbl = tk.Label(cam_box, bg="black")
    video_lbl.pack(fill="both", expand=True, padx=5, pady=5)

    # Footer
    footer = tk.Frame(scrollable_frame, bg="#f4f7f6")
    footer.pack(fill="x", pady=20)

    tk.Button(footer, text="⬅ Back", command=back_to_dash, bg="#95a5a6", fg="white", width=15).pack(side="left", padx=40)
    tk.Button(footer, text="✅ REGISTER & CAPTURE", command=start_process, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="right", padx=40)