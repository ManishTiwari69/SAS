import datetime
import os
import time
import cv2
import pandas as pd
from db_config import get_db_connection
from tkinter import messagebox

def get_student_details():
    """Fetches full details directly from MySQL for the student log."""
    details_dict = {}
    try:
        db = get_db_connection()
        cursor = db.cursor()
        # Fetching Full Name and Role now
        cursor.execute("SELECT id, full_name, role FROM students")
        results = cursor.fetchall()
        for (sid, fname, srole) in results:
            details_dict[int(sid)] = {"name": fname, "role": srole}
        db.close()
    except Exception as e:
        print(f"⚠️ Error: {e}")
    return details_dict

def mark_attendance_mysql(student_id, date_str, time_str):
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    if cursor.fetchone() is None:
        db.close()
        return None 

    check_sql = "SELECT * FROM attendance_log WHERE student_id = %s AND date = %s"
    cursor.execute(check_sql, (student_id, date_str))
    
    if cursor.fetchone() is None:
        insert_sql = "INSERT INTO attendance_log (student_id, date, time) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (student_id, date_str, time_str))
        db.commit()
        db.close()
        return True  
    else:
        db.close()
        return False 

def recognize_attendence():
    # Setup Recognizer - NOW POINTING TO STUDENT DATA
    recognizer = cv2.face.LBPHFaceRecognizer_create()  
    trainer_path = "TrainingImageLabel" + os.sep + "StudentTrainner.yml"
    
    if not os.path.exists(trainer_path):
        messagebox.showerror("Error", "Student training data not found! Please register students and train first.")
        return

    recognizer.read(trainer_path)
    faceCascade = cv2.CascadeClassifier("haarcascade_default.xml")
    
    # Load data from MySQL
    student_details = get_student_details()
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    attendance_list = [] 
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    already_handled_in_session = [] 

    print("--- Student Attendance Mode Active ---")

    while True:
        ret, im = cam.read()
        if not ret: break
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(64, 64))

        for (x, y, w, h) in faces:
            Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            match_confidence = round(100 - conf)

            # Verification logic
            if Id in student_details and match_confidence > 65:
                full_name = student_details[Id]["name"]
                role = student_details[Id]["role"]
                
                ts = time.time()
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

                if Id not in already_handled_in_session:
                    status = mark_attendance_mysql(Id, date, timestamp)
                    if status is True:
                        print(f"✅ Recorded: {full_name} ({role})")
                        attendance_list.append([Id, full_name, date, timestamp])
                    elif status is False:
                        messagebox.showinfo("Status", f"{full_name} is already marked.")
                    already_handled_in_session.append(Id)
                
                color = (0, 255, 0)
                label = f"{full_name} ({role})"
            else:
                color = (0, 0, 255)
                label = "Unknown"

            cv2.rectangle(im, (x, y), (x+w, y+h), color, 2)
            cv2.putText(im, label, (x+5, y-5), font, 0.7, (255, 255, 255), 2)

        cv2.imshow('Attendance System', im)
        if cv2.waitKey(1) == ord('q'):
            break

    # Save Session Backup
    if attendance_list:
        if not os.path.exists("Attendance"): os.makedirs("Attendance")
        df = pd.DataFrame(attendance_list, columns=['Id', 'Name', 'Date', 'Time'])
        filename = f"Attendance{os.sep}Backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)

    cam.release()
    cv2.destroyAllWindows()