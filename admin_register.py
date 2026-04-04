import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import cv2
import os
import shutil
import bcrypt
from db_config import get_db_connection

UPLOAD_DIR = "Admin_Profiles"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def register_admin(container):
    # 1. Clear existing widgets in the content area
    for widget in container.winfo_children():
        widget.destroy()

    # REMOVED: container.title, container.geometry, container.configure
    # These belong to the main window, not this Frame.

    # Variables
    selected_pic_relative_path = tk.StringVar()
    gender_var = tk.StringVar(value="Male")
    is_capturing = [False] 
    cap = [None]

    # --- Header (Now relative to container) ---
    header = tk.Frame(container, bg="#3498db", height=60)
    header.pack(side="top", fill="x")
    tk.Label(header, text="🛡️ NEW ADMIN REGISTRATION", font=("Arial", 16, "bold"), 
             bg="#3498db", fg="white").pack(pady=15)

    # --- Main Container ---
    main_frame = tk.Frame(container, bg="#f4f7f6")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # LEFT COLUMN
    left_column = tk.Frame(main_frame, bg="#f4f7f6")
    left_column.pack(side="left", fill="both", expand=True, padx=5)

    form_frame = tk.LabelFrame(left_column, text="Admin Details", bg="white", font=("Arial", 10, "bold"), padx=15, pady=10)
    form_frame.pack(fill="x", pady=5)

    ents = {}
    def create_field(label, row, is_pass=False):
        tk.Label(form_frame, text=label, bg="white").grid(row=row, column=0, pady=5, sticky="w")
        entry = tk.Entry(form_frame, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "", width=28)
        entry.grid(row=row, column=1, pady=5, padx=10)
        return entry

    ents['user'] = create_field("Username:", 0)
    ents['pass'] = create_field("Password:", 1, is_pass=True)
    ents['fname'] = create_field("First Name:", 2)
    ents['lname'] = create_field("Last Name:", 3)

    tk.Label(form_frame, text="DOB:", bg="white").grid(row=4, column=0, pady=5, sticky="w")
    ents['dob'] = DateEntry(form_frame, width=26, background='darkblue', foreground='white', borderwidth=2)
    ents['dob'].grid(row=4, column=1, pady=5, padx=10)
    ents['phone'] = create_field("Phone No:", 5)

    tk.Label(form_frame, text="Gender:", bg="white").grid(row=6, column=0, pady=5, sticky="w")
    tk.OptionMenu(form_frame, gender_var, "Male", "Female", "Other").grid(row=6, column=1, pady=5, padx=10, sticky="ew")

    tk.Label(form_frame, text="Address:", bg="white").grid(row=7, column=0, pady=5, sticky="nw")
    addr_txt = tk.Text(form_frame, height=3, width=21, font=("Arial", 10), bg="#f0f2f5")
    addr_txt.grid(row=7, column=1, pady=5, padx=10)

    # --- Profile Preview ---
    preview_lbl = tk.Label(left_column, text="No Image", bg="#dfe6e9", width=20, height=10)
    preview_lbl.pack(pady=5)
    
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

    tk.Button(left_column, text="📁 Upload Photo", command=upload_image, bg="#34495e", fg="white").pack(fill="x")

    # RIGHT COLUMN (Face Capture)
    right_column = tk.Frame(main_frame, bg="#f4f7f6")
    right_column.pack(side="right", fill="both", expand=True, padx=10)
    
    cam_box = tk.LabelFrame(right_column, text="Internal Face Capture", bg="white", font=("Arial", 10, "bold"))
    cam_box.pack(fill="both", expand=True)
    video_lbl = tk.Label(cam_box, bg="black")
    video_lbl.pack(fill="both", expand=True, padx=5, pady=5)

    sample_count = [0]
    face_detector = cv2.CascadeClassifier("haarcascade_default.xml")

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
        if not ents['user'].get() or not ents['pass'].get():
            messagebox.showerror("Error", "Enter Username and Password first!")
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
            
            sql = "INSERT INTO admin_details (admin_id, first_name, last_name, dob, gender, address, phone_no, profile_pic_path) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(sql, (admin_id, ents['fname'].get(), ents['lname'].get(), ents['dob'].get_date(), gender_var.get(), addr_txt.get("1.0", "end-1c"), ents['phone'].get(), selected_pic_relative_path.get()))
            
            db.commit()
            db.close()
            messagebox.showinfo("Success", "Admin Registration Complete!")
            back_to_dash()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")

    # --- Footer ---
    footer = tk.Frame(container, bg="#f4f7f6")
    footer.pack(side="bottom", fill="x", pady=20)

    def back_to_dash():
        if cap[0]: cap[0].release()
        root = container.winfo_toplevel()
        import main
        main.render_dashboard(root)

    tk.Button(footer, text="⬅ Back", command=back_to_dash, bg="#95a5a6", fg="white", width=15).pack(side="left", padx=40)
    tk.Button(footer, text="✅ REGISTER & CAPTURE", command=start_process, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="right", padx=40)