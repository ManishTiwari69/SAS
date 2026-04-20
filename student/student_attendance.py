import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection

PRIMARY_COLOR = "#00d084"
BG_COLOR      = "#f8f9fa"


def show_attendance(container, student_id):
    """Render the attendance view into container."""

    # Stat cards
    stats = _get_stats(student_id)

    card_frame = tk.Frame(container, bg=BG_COLOR)
    card_frame.pack(fill="x", padx=30, pady=25)

    _stat_card(card_frame, "TOTAL CLASSES", stats["total"],   "#ffffff", "#333",        0)
    _stat_card(card_frame, "PRESENT",       stats["present"], PRIMARY_COLOR, "white",   1)
    _stat_card(card_frame, "ABSENT",        stats["absent"],  "#e74c3c", "white",       2)
    _stat_card(card_frame, "ATTENDANCE %",  f"{stats['pct']}%", "#3498db", "white",    3)

    # Table frame
    table_frame = tk.LabelFrame(
        container, text="  My Attendance Records  ",
        font=("Arial", 12, "bold"),
        bg="white", bd=1, relief="solid")
    table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    # Treeview style
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Att.Treeview",
                    background="white", foreground="#333",
                    rowheight=30, fieldbackground="white",
                    font=("Arial", 10))
    style.configure("Att.Treeview.Heading",
                    font=("Arial", 10, "bold"), background="#f0f0f0")
    style.map("Att.Treeview", background=[("selected", PRIMARY_COLOR)])

    columns = ("No.", "Date", "Status", "Time In")
    tree = ttk.Treeview(table_frame, columns=columns,
                        show="headings", style="Att.Treeview")

    widths = {"No.": 60, "Date": 180, "Status": 150, "Time In": 180}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=widths[col])

    tree.tag_configure("Present", foreground="#27ae60", font=("Arial", 10, "bold"))
    tree.tag_configure("Absent",  foreground="#e74c3c", font=("Arial", 10, "bold"))
    tree.tag_configure("Late",    foreground="#e67e22", font=("Arial", 10, "bold"))

    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scroll.set)

    tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    scroll.pack(side="right", fill="y", pady=10, padx=(0, 10))

    # Load rows
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT log_date, status, log_time
            FROM attendance_logs
            WHERE student_id = %s
            ORDER BY log_date DESC, log_time DESC
        """, (student_id,))
        rows = cursor.fetchall()
        db.close()

        for i, (log_date, status, log_time) in enumerate(rows, start=1):
            tag = status if status in ("Present", "Absent", "Late") else ""
            tree.insert("", "end", values=(i, log_date, status, log_time), tags=(tag,))

    except Exception as e:
        messagebox.showerror("DB Error", f"Could not load attendance:\n{e}")


# ── helpers ───────────────────────────────────────────────────────────────

def _stat_card(parent, title, value, bg, fg, col):
    card = tk.Frame(parent, bg=bg, width=180, height=110,
                    highlightthickness=1, highlightbackground="#ddd")
    card.grid(row=0, column=col, padx=12)
    card.grid_propagate(False)
    tk.Label(card, text=title, font=("Arial", 9, "bold"),
             bg=bg, fg="#aaa" if bg == "#ffffff" else "white").pack(pady=(22, 4))
    tk.Label(card, text=str(value), font=("Arial", 24, "bold"),
             bg=bg, fg=fg).pack()


def _get_stats(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM attendance_logs WHERE student_id = %s",
            (student_id,))
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM attendance_logs WHERE student_id = %s AND status = 'Present'",
            (student_id,))
        present = cursor.fetchone()[0]

        db.close()
        absent = total - present
        pct    = round((present / total * 100), 1) if total > 0 else 0
        return {"total": total, "present": present, "absent": absent, "pct": pct}

    except Exception:
        return {"total": 0, "present": 0, "absent": 0, "pct": 0}
