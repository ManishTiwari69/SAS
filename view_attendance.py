import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection

def show_attendance():
    # 1. Setup the Window
    view_window = tk.Toplevel()
    view_window.title("Attendance Records")
    view_window.geometry("800x400")
    view_window.configure(bg="#2c3e50")

    title = tk.Label(view_window, text="DAILY ATTENDANCE LOG", 
                     bg="#2c3e50", fg="white", font=('times', 20, 'bold'))
    title.pack(pady=10)

    # 2. Create the Table (Treeview)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#ecf0f1", foreground="black", rowheight=25, fieldbackground="#ecf0f1")
    style.map("Treeview", background=[('selected', '#3498db')])

    tree_frame = tk.Frame(view_window)
    tree_frame.pack(pady=10, padx=20, fill="both", expand=True)

    columns = ("ID", "Name", "Date", "Time")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    
    # Define Headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    
    tree.pack(side="left", fill="both", expand=True)

    # Add Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # 3. Fetch Data from MySQL
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # We use a JOIN to get the Name from the students table
        query = """
            SELECT a.student_id, s.name, a.date, a.time 
            FROM attendance_log a 
            JOIN students s ON a.student_id = s.id 
            ORDER BY a.date DESC, a.time DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

        db.close()
    except Exception as e:
        messagebox.showerror("DB Error", f"Could not fetch records: {e}")

    # Close button
    btn_close = tk.Button(view_window, text="Close", command=view_window.destroy, 
                          bg="#e74c3c", fg="white", width=20)
    btn_close.pack(pady=10)