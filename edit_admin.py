import tkinter as tk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import os
import shutil
import bcrypt
from db_config import get_db_connection
from validate import AdminValidator

UPLOAD_DIR = "Admin_Profiles"

def edit_admin(container, admin_id, on_back_callback):
    # 1. Clear everything
    for widget in container.winfo_children():
        widget.destroy()

    # Setup Scrollable Infrastructure (Same as register)
    canvas = tk.Canvas(container, bg="#f4f7f6", highlightthickness=0)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#f4f7f6")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=800)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Variables ---
    selected_pic_relative_path = tk.StringVar()
    ents = {}
    err_lbls = {}

    # --- Logic: Fetch Existing Data ---
    def load_admin_data():
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT a.username, d.* FROM admins a 
                JOIN admin_details d ON a.id = d.admin_id 
                WHERE a.id = %s
            """
            cursor.execute(query, (admin_id,))
            data = cursor.fetchone()
            db.close()

            if data:
                ents['user'].insert(0, data['username'])
                ents['fname'].insert(0, data['first_name'])
                ents['lname'].insert(0, data['last_name'])
                ents['phone'].insert(0, data['phone_no'])
                ents['email'].insert(0, data['email'])
                ents['dob'].set_date(data['dob'])
                ents['addr'].insert("1.0", data['address'])
                
                if data['profile_pic_path'] and os.path.exists(data['profile_pic_path']):
                    img = Image.open(data['profile_pic_path']).resize((150, 150), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    preview_lbl.config(image=photo, text="")
                    preview_lbl.image = photo
                    selected_pic_relative_path.set(data['profile_pic_path'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def update_process():
        # Validate data (similar to register, but password can be optional)
        admin_data = {
            'user': ents['user'].get().strip(),
            'fname': ents['fname'].get().strip(),
            'lname': ents['lname'].get().strip(),
            'email': ents['email'].get().strip(),
            'phone': ents['phone'].get().strip(),
            'addr': ents['addr'].get("1.0", "end-1c").strip(),
            'pic_path': selected_pic_relative_path.get()
        }
        
        try:
            db = get_db_connection()
            cursor = db.cursor()
            
            # Update Username
            cursor.execute("UPDATE admins SET username=%s WHERE id=%s", (admin_data['user'], admin_id))
            
            # Update Details
            sql = """UPDATE admin_details SET first_name=%s, last_name=%s, dob=%s, 
                     email=%s, address=%s, phone_no=%s, profile_pic_path=%s WHERE admin_id=%s"""
            cursor.execute(sql, (admin_data['fname'], admin_data['lname'], ents['dob'].get_date(), 
                                 admin_data['email'], admin_data['addr'], admin_data['phone'], 
                                 admin_data['pic_path'], admin_id))
            
            # Handle Password separately (only if user typed something new)
            new_pass = ents['pass'].get()
            if new_pass:
                hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("UPDATE admins SET password=%s WHERE id=%s", (hashed, admin_id))

            db.commit()
            db.close()
            messagebox.showinfo("Success", "Profile Updated Successfully!")
            on_back_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {str(e)}")

    # --- Build UI (Shortened for brevity, use same styling as register) ---
    header = tk.Frame(scrollable_frame, bg="#2980b9", height=60)
    header.pack(fill="x")
    tk.Label(header, text="👤 EDIT ADMIN PROFILE", font=("Arial", 14, "bold"), bg="#2980b9", fg="white").pack(pady=15)

    form_frame = tk.LabelFrame(scrollable_frame, text="Update Information", bg="white", padx=15, pady=10)
    form_frame.pack(fill="x", padx=20, pady=10)

    def create_field(label, row, is_pass=False):
        tk.Label(form_frame, text=label, bg="white").grid(row=row, column=0, sticky="w")
        entry = tk.Entry(form_frame, font=("Arial", 10), bg="#f0f2f5", show="*" if is_pass else "", width=40)
        entry.grid(row=row, column=1, pady=5, padx=10)
        return entry

    ents['user'] = create_field("Username:", 0)
    ents['pass'] = create_field("New Password (Leave blank to keep current):", 1, is_pass=True)
    ents['fname'] = create_field("First Name:", 2)
    ents['lname'] = create_field("Last Name:", 3)
    ents['phone'] = create_field("Phone No:", 4)
    ents['email'] = create_field("Email:", 5)
    
    tk.Label(form_frame, text="DOB:", bg="white").grid(row=6, column=0, sticky="w")
    ents['dob'] = DateEntry(form_frame, width=38)
    ents['dob'].grid(row=6, column=1, pady=5, padx=10)

    tk.Label(form_frame, text="Address:", bg="white").grid(row=7, column=0, sticky="nw")
    ents['addr'] = tk.Text(form_frame, height=3, width=30, font=("Arial", 10), bg="#f0f2f5")
    ents['addr'].grid(row=7, column=1, pady=5, padx=10)

    preview_lbl = tk.Label(scrollable_frame, text="No Image", bg="#dfe6e9", width=20, height=10)
    preview_lbl.pack(pady=5)

    # Footer
    footer = tk.Frame(scrollable_frame, bg="#f4f7f6")
    footer.pack(fill="x", pady=20)
    tk.Button(footer, text="⬅ Cancel", command=on_back_callback, bg="#95a5a6", fg="white", width=15).pack(side="left", padx=40)
    tk.Button(footer, text="💾 SAVE CHANGES", command=update_process, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), width=25).pack(side="right", padx=40)

    load_admin_data()