import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection
from datetime import date as dt_date
from tkcalendar import DateEntry  # Ensure you have installed: pip install tkcalendar

PRIMARY_COLOR = "#00d084"
BG_COLOR      = "#f8f9fa"

def show_leave_apply(container, student_id):
    """Render the Leave Application form into container."""

    wrapper = tk.Frame(container, bg=BG_COLOR)
    wrapper.pack(fill="both", expand=True, padx=60, pady=40)

    form = tk.LabelFrame(
        wrapper, text="  Apply for Leave  ",
        font=("Arial", 14, "bold"),
        bg="white", bd=1, relief="solid")
    form.pack(fill="x", pady=10)
    form.columnconfigure(0, weight=1)

    # --- Reason ---
    tk.Label(form, text="Reason for Leave:", font=("Arial", 11, "bold"),
             bg="white", fg="#555").grid(row=0, column=0, sticky="w", padx=25, pady=(25, 4))

    reason_ent = tk.Entry(form, font=("Arial", 12), bg="#f0f4ff", relief="flat",
                          highlightthickness=1, highlightbackground="#c0c8ff")
    reason_ent.grid(row=1, column=0, sticky="ew", padx=25, ipady=8)

    # --- Leave Type ---
    tk.Label(form, text="Leave Type:", font=("Arial", 11, "bold"),
             bg="white", fg="#555").grid(row=2, column=0, sticky="w", padx=25, pady=(15, 4))

    leave_type_var = tk.StringVar(value="Sick Leave")
    type_menu = ttk.Combobox(
        form, textvariable=leave_type_var,
        values=["Sick Leave", "Personal Leave", "Family Emergency", "Other"],
        font=("Arial", 12), state="readonly")
    type_menu.grid(row=3, column=0, sticky="ew", padx=25, ipady=5)

    # --- From Date (Picker) ---
    tk.Label(form, text="From Date:", font=("Arial", 11, "bold"),
             bg="white", fg="#555").grid(row=4, column=0, sticky="w", padx=25, pady=(15, 4))

    start_ent = DateEntry(form, font=("Arial", 12), background='darkblue',
                          foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    start_ent.grid(row=5, column=0, sticky="ew", padx=25, ipady=5)

    # --- To Date (Picker) ---
    tk.Label(form, text="To Date:", font=("Arial", 11, "bold"),
             bg="white", fg="#555").grid(row=6, column=0, sticky="w", padx=25, pady=(15, 4))

    end_ent = DateEntry(form, font=("Arial", 12), background='darkblue',
                        foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    end_ent.grid(row=7, column=0, sticky="ew", padx=25, ipady=5, pady=(0, 20))

    # --- Submit Button ---
    def submit():
        reason     = reason_ent.get().strip()
        leave_type = leave_type_var.get()
        # .get_date() returns a datetime.date object directly
        start_date = start_ent.get_date()
        end_date   = end_ent.get_date()

        if not reason:
            messagebox.showwarning("Input Error", "Please provide a reason.")
            return
            
        if start_date > end_date:
            messagebox.showwarning("Input Error", "Start date cannot be after end date.")
            return

        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO leave_applications
                    (student_id, reason, leave_type, leave_start, leave_end, status, applied_on)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (student_id, reason, leave_type, start_date, end_date,
                  "Pending", dt_date.today()))
            db.commit()
            db.close()

            messagebox.showinfo("Success", "Leave application submitted!")
            reason_ent.delete(0, tk.END)
            leave_type_var.set("Sick Leave")

        except Exception as e:
            messagebox.showerror("Database Error", f"Could not submit leave:\n{e}")

    tk.Button(
        form, text="✅  Submit Leave Application",
        bg=PRIMARY_COLOR, fg="white",
        font=("Arial", 12, "bold"), bd=0, pady=12,
        cursor="hand2", command=submit
    ).grid(row=8, column=0, sticky="ew", padx=25, pady=(0, 25))
