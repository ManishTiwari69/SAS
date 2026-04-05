import csv
import cv2
import os
import tkinter as tk
from PIL import Image, ImageTk
from db_config import get_db_connection
from tkinter import simpledialog, messagebox

def register_student_camera(container, on_close_callback):
    """Refactored version of takeImages to show in the dashboard window"""
    
    # 1. Clear the content area
    for widget in container.winfo_children():
        widget.destroy()

    # UI Setup inside the dashboard
    header = tk.Frame(container, bg="#2c3e50", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="📸 FACE ENROLLMENT", font=("Arial", 14, "bold"), bg="#2c3e50", fg="white").pack(pady=10)

    video_frame = tk.Label(container, bg="black", width=640, height=480)
    video_frame.pack(pady=20)

    # State variables
    sample_count = [0]
    cap = [cv2.VideoCapture(0)]
    detector = cv2.CascadeClassifier("haarcascade_default.xml")
    
    # Get ID and Name via dialogs
    Id = simpledialog.askstring("Input", "Enter Your Id:")
    Name = simpledialog.askstring("Input", "Enter Your Name:")

    if not Id or not Name or not Id.isdigit():
        messagebox.showerror("Error", "Invalid ID or Name.")
        cap[0].release()
        return

    def update_frame():
        if sample_count[0] < 100:
            ret, frame = cap[0].read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    sample_count[0] += 1
                    # Save Image
                    if not os.path.exists("TrainingImage"): os.makedirs("TrainingImage")
                    img_path = f"TrainingImage{os.sep}{Name}.{Id}.{sample_count[0]}.jpg"
                    cv2.imwrite(img_path, gray[y:y+h, x:x+w])
                    
                    # Draw rectangle for feedback
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Samples: {sample_count[0]}/100", (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Convert frame to Tkinter Image
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((640, 480), Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                video_frame.imgtk = imgtk
                video_frame.configure(image=imgtk)

                container.after(10, update_frame)
            else:
                finalize()
        else:
            finalize()

    def finalize():
        cap[0].release()
        save_student_to_mysql(Id, Name)
        save_to_csv_backup(Id, Name)
        messagebox.showinfo("Success", f"Registration complete for {Name}")
        # Return to main dashboard overview
        import main
        main.render_dashboard(container.winfo_toplevel())

    update_frame()

# --- Helper Functions (Keep these as you have them) ---

def save_student_to_mysql(Id, name):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        sql = "INSERT INTO students (id, name) VALUES (%s, %s)"
        cursor.execute(sql, (int(Id), name))
        db.commit()
        db.close()
    except Exception as e:
        messagebox.showerror("DB Error", f"Database Error: {e}")

def save_to_csv_backup(Id, name):
    if not os.path.exists("StudentDetails"): os.makedirs("StudentDetails")
    file_path = "StudentDetails" + os.sep + "StudentDetails.csv"
    with open(file_path, 'a+', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([Id, name])