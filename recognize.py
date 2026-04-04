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

def recognize_attendance(container):
    # 1. Path Synchronization
    # These MUST match what you used in update_student.py
    trainer_path = "TrainingImageLabel/StudentTrainner.yml"
    image_dir = "StudentTrainingImage" # Fixed: Was "TrainingImage"

    if not os.path.exists(trainer_path):
        if os.path.exists(image_dir) and len(os.listdir(image_dir)) > 0:
            print("🚀 Trainer missing. Starting auto-training...")
            TrainImages(training_type="student") 
        else:
            messagebox.showerror("Error", "No training images found in 'StudentTrainingImage'!")
            return

    # 2. UI Reset
    for widget in container.winfo_children():
        widget.destroy()

    header = tk.Frame(container, bg="#2c3e50", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="🛡️ SMART ATTENDANCE SCANNER", font=("Arial", 14, "bold"), 
             bg="#2c3e50", fg="white").pack(pady=10)

    video_frame = tk.Label(container, bg="black")
    video_frame.pack(pady=20)

    # 3. Setup Recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(trainer_path)
    faceCascade = cv2.CascadeClassifier("haarcascade_default.xml")
    student_details = get_student_details()
    
    cap = [cv2.VideoCapture(0, cv2.CAP_DSHOW)]
    already_handled_in_session = []
    attendance_list = []

    def update_frame():
        ret, im = cap[0].read()
        if not ret: return

        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            # Predict returns ID and Confidence (lower is better/more confident)
            Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            match_confidence = round(100 - conf)

            # Check if ID exists in our fetched dictionary
            if Id in student_details and match_confidence > 50: # Slightly lower threshold for better recognition
                full_name = student_details[Id]["name"]
                
                ts = time.time()
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

                if Id not in already_handled_in_session:
                    status = mark_attendance_mysql(Id, date, timestamp)
                    if status is True:
                        attendance_list.append([Id, full_name, date, timestamp])
                    already_handled_in_session.append(Id)
                
                label = f"{full_name} ({match_confidence}%)"
                color = (0, 255, 0)
            else:
                label = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(im, (x, y), (x+w, y+h), color, 2)
            cv2.putText(im, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Update Display
        img = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img).resize((700, 500), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        video_frame.imgtk = imgtk
        video_frame.configure(image=imgtk)
        video_frame.after(10, update_frame)

    def stop_scanner():
        cap[0].release()
        if attendance_list:
            if not os.path.exists("Attendance"): os.makedirs("Attendance")
            df = pd.DataFrame(attendance_list, columns=['Id', 'Name', 'Date', 'Time'])
            filename = f"Attendance/Backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
        
        # Return to main dashboard (make sure main.py has this function)
        try:
            import main
            main.render_dashboard(container.winfo_toplevel())
        except:
            container.destroy()

    tk.Button(container, text="⏹️ Stop Scanner", command=stop_scanner, 
              bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), width=25).pack(pady=10)

    update_frame()