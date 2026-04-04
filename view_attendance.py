import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection

def show_attendance(container): # 1. Accept the container
    # 2. Clear the previous content in the main dashboard area
    for widget in container.winfo_children():
        widget.destroy()

    # 3. Use 'container' as the parent instead of 'view_window'
    main_frame = tk.Frame(container, bg="#2c3e50")
    main_frame.pack(fill="both", expand=True)

    title = tk.Label(main_frame, text="DAILY ATTENDANCE LOGS", 
                     bg="#2c3e50", fg="white", font=('times', 20, 'bold'))
    title.pack(pady=10)

    # 2. Create the Table (Treeview)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#ecf0f1", foreground="black", rowheight=25, fieldbackground="#ecf0f1")
    style.map("Treeview", background=[('selected', '#3498db')])

    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(pady=10, padx=20, fill="both", expand=True)

    # Updated columns to match your new table structure + Student Name
    columns = ("ID", "Name", "Status", "Date", "Time")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    
    # Define Headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=120)
    
    tree.pack(side="left", fill="both", expand=True)

    # Add Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # 3. Fetch Data from MySQL
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Updated Query: 
        # Joining attendance_logs with student_profiles to get the full name
        query = """
            SELECT a.student_id, CONCAT(p.first_name, ' ', p.last_name) AS full_name, 
                   a.status, a.log_date, a.log_time 
            FROM attendance_logs a 
            JOIN student_profiles p ON a.student_id = p.student_id 
            ORDER BY a.log_date DESC, a.log_time DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

        db.close()
    except Exception as e:
        messagebox.showerror("DB Error", f"Could not fetch records: {e}")

    # Close button
    btn_close = tk.Button(view_window, text="Close Window", command=view_window.destroy, 
                          bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=20)
    btn_close.pack(pady=15)