import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection

def show_leave_requests(container):
    # Clear previous content
    for widget in container.winfo_children():
        widget.destroy()

    header = tk.Label(container, text="All Leave Applications", font=("Arial", 18, "bold"), bg="white")
    header.pack(pady=20)

    # --- Table Setup ---
    cols = ("ID", "Student", "Type", "Start", "End", "Reason", "Status")
    tree = ttk.Treeview(container, columns=cols, show="headings", height=15)
    
    # Define row tags for colors
    tree.tag_configure('Pending', foreground="orange")
    tree.tag_configure('Approved', foreground="green")
    tree.tag_configure('Rejected', foreground="red")

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor="center")
    
    tree.column("Reason", width=250)
    tree.pack(fill="both", expand=True, padx=20)

    def load_data():
        for item in tree.get_children():
            tree.delete(item)
        try:
            db = get_db_connection()
            cursor = db.cursor()
            # Removed the 'Pending' filter to show everything
            cursor.execute("""
                SELECT l.id, s.username, l.leave_type, l.leave_start, l.leave_end, l.reason, l.status 
                FROM leave_applications l
                JOIN students s ON l.student_id = s.student_id
                ORDER BY l.id DESC
            """)
            for row in cursor.fetchall():
                status = row[6] # Get the status value
                tree.insert("", "end", values=row, tags=(status,))
            db.close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load requests: {e}")

    def update_status(new_status):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a request first.")
            return
        
        values = tree.item(selected)['values']
        request_id = values[0]
        current_status = values[6]

        if current_status != "Pending":
            if not messagebox.askyesno("Confirm", f"This request is already {current_status}. Change it to {new_status}?"):
                return
        
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("UPDATE leave_applications SET status = %s WHERE id = %s", (new_status, request_id))
            db.commit()
            db.close()
            messagebox.showinfo("Success", f"Request marked as {new_status}!")
            load_data() 
        except Exception as e:
            messagebox.showerror("Error", f"Update failed: {e}")

    # --- Buttons ---
    btn_frame = tk.Frame(container, bg="white")
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="✅ Approve", bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
              width=15, cursor="hand2", command=lambda: update_status("Approved")).pack(side="left", padx=10)
    
    tk.Button(btn_frame, text="❌ Reject", bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
              width=15, cursor="hand2", command=lambda: update_status("Rejected")).pack(side="left", padx=10)

    load_data()
