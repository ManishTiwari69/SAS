import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection


def show_leave_history(container, student_id):
    """Render the Leave History table into container."""

    frame = tk.LabelFrame(
        container, text="  My Leave Applications  ",
        font=("Arial", 12, "bold"),
        bg="white", bd=1, relief="solid")
    frame.pack(fill="both", expand=True, padx=30, pady=25)

    # Style
    style = ttk.Style()
    style.configure("LHist.Treeview",
                    background="white", foreground="#333",
                    rowheight=30, fieldbackground="white",
                    font=("Arial", 10))
    style.configure("LHist.Treeview.Heading",
                    font=("Arial", 10, "bold"), background="#f0f0f0")
    style.map("LHist.Treeview", background=[("selected", "#3498db")])

    columns = ("No.", "From", "To", "Type", "Reason", "Applied On", "Status")
    tree = ttk.Treeview(frame, columns=columns, show="headings", style="LHist.Treeview")

    widths = {"No.": 50, "From": 120, "To": 120, "Type": 130,
              "Reason": 200, "Applied On": 120, "Status": 100}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=widths[col])

    # Status colour tags
    tree.tag_configure("Pending",  foreground="#e67e22", font=("Arial", 10, "bold"))
    tree.tag_configure("Approved", foreground="#27ae60", font=("Arial", 10, "bold"))
    tree.tag_configure("Rejected", foreground="#e74c3c", font=("Arial", 10, "bold"))

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll.set)

    tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

    # Load rows
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT leave_start, leave_end, leave_type, reason, applied_on, status
            FROM leave_applications
            WHERE student_id = %s
            ORDER BY applied_on DESC
        """, (student_id,))
        rows = cursor.fetchall()
        db.close()

        for i, (start, end, ltype, reason, applied, status) in enumerate(rows, start=1):
            tag = status if status in ("Pending", "Approved", "Rejected") else ""
            tree.insert("", "end",
                        values=(i, start, end, ltype, reason, applied, status),
                        tags=(tag,))

    except Exception as e:
        messagebox.showerror("DB Error", f"Could not load leave history:\n{e}")
