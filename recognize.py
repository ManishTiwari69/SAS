import datetime
import os
import time
import cv2
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk
from db_config import get_db_connection
from tkinter import messagebox
from train_image import TrainImages
from threading import Thread

def get_student_details():
    """Fetches name and role from the joined database tables."""
    details_dict = {}
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # FIX: Ensure there is NO COMMA after s.role
        query = """
            SELECT s.student_id, p.first_name, p.last_name
            FROM students s
            JOIN student_profiles p ON s.student_id = p.student_id
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        for (sid, fname, lname) in results:
            full_name = f"{fname} {lname}"
            details_dict[int(sid)] = {"name": full_name}
        db.close()
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
    return details_dict

def mark_attendance_mysql(student_id, date_str, time_str):
    """Marks attendance in the log table with the new schema: student_id, status, log_date, log_time"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # 1. Check if student exists in the students table
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        if cursor.fetchone() is None:
            db.close()
            return None 

        # 2. Prevent double attendance for the same day
        # Using log_date to match your new schema
        check_sql = "SELECT * FROM attendance_logs WHERE student_id = %s AND log_date = %s"
        cursor.execute(check_sql, (student_id, date_str))
        
        if cursor.fetchone() is None:
            # 3. Insert into the new schema
            # log_id is likely AUTO_INCREMENT, so we skip it. Status is set to 'Present'
            insert_sql = """
                INSERT INTO attendance_logs (student_id, status, log_date, log_time) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (student_id, 'Present', date_str, time_str))
            db.commit()
            db.close()
            return True  
        else:
            db.close()
            return False 
    except Exception as e:
        print(f"⚠️ Attendance Log Error: {e}")
        return False

def recognize_attendance(main_root, on_close_callback=None):
    """
    main_root: The main Tkinter window (to keep the app alive)
    on_close_callback: Function to refresh dashboard stats when camera closes
    """
    trainer_path = "TrainingImageLabel/StudentTrainner.yml"
    
    # 1. Initial Checks
    if not os.path.exists(trainer_path):
        messagebox.showerror("Error", "Trainer not found! Please train the system first.")
        return

    # 2. Create a NEW Independent Window for the Camera
    cam_window = tk.Toplevel(main_root)
    cam_window.title("🛡️ Smart Attendance Scanner")
    cam_window.geometry("800x700")
    cam_window.protocol("WM_DELETE_WINDOW", lambda: stop_scanner()) # Handle "X" click

    header = tk.Frame(cam_window, bg="#2c3e50", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="SYSTEM RUNNING IN BACKGROUND", font=("Arial", 12, "bold"), 
             bg="#2c3e50", fg="#00d084").pack(pady=10)

    video_frame = tk.Label(cam_window, bg="black")
    video_frame.pack(pady=10)

    # 3. Setup Recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(trainer_path)
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    student_details = get_student_details()
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    already_handled_in_session = []
    attendance_list = []
    running = [True]

    def update_loop():
        """This runs in the background but updates the specific cam_window UI."""
        while running[0]:
            ret, im = cap.read()
            if not ret: break

            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                match_confidence = round(100 - conf)

                if Id in student_details and match_confidence > 50:
                    full_name = student_details[Id]["name"]
                    ts = time.time()
                    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

                    # logic for status tag
                    status_tag = ""
                    if Id not in already_handled_in_session:
                        status = mark_attendance_mysql(Id, date, timestamp)
                        already_handled_in_session.append(Id)
                        if status:
                            attendance_list.append([Id, full_name, date, timestamp])
                            status_tag = " - PRESENT"
                        else:
                            status_tag = " - ALREADY MARKED"
                    else:
                        status_tag = " - ALREADY MARKED"

                    label = f"{full_name} ({match_confidence}%){status_tag}"
                    color = (0, 255, 0)
                else:
                    label = "Unknown"
                    color = (0, 0, 255)

                cv2.rectangle(im, (x, y), (x+w, y+h), color, 2)
                cv2.putText(im, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Convert to PhotoImage and update the window
            try:
                img = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((700, 500), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                video_frame.imgtk = imgtk
                video_frame.configure(image=imgtk)
            except:
                break # Window was likely closed

    def stop_scanner():
        running[0] = False
        cap.release()
        
        # Save Backup
        if attendance_list:
            if not os.path.exists("Attendance"): os.makedirs("Attendance")
            df = pd.DataFrame(attendance_list, columns=['Id', 'Name', 'Date', 'Time'])
            filename = f"Attendance/Backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
        
        cam_window.destroy()
        if on_close_callback:
            on_close_callback()

    tk.Button(cam_window, text="⏹️ Close & Save Attendance", command=stop_scanner, 
              bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=30).pack(pady=10)

    # Start the camera loop in a background thread
    Thread(target=update_loop, daemon=True).start()