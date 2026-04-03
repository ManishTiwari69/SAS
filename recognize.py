import datetime
import os
import time
import cv2
import pandas as pd
from db_config import get_db_connection
from tkinter import messagebox

def get_student_names():
    """Fetches all registered students and returns a dictionary {id: name}."""
    student_dict = {}
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, name FROM students")
        results = cursor.fetchall()
        for (sid, sname) in results:
            student_dict[int(sid)] = sname
        db.close()
    except Exception as e:
        print(f"⚠️ Error fetching student list from MySQL: {e}")
    return student_dict

def mark_attendance_mysql(student_id, date_str, time_str):
    db = get_db_connection()
    cursor = db.cursor()
    
    # 1. VALIDATION: Check if student exists
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    if cursor.fetchone() is None:
        db.close()
        return None 

    # 2. DUPLICATE CHECK: Today's attendance
    check_sql = "SELECT * FROM attendance_log WHERE student_id = %s AND date = %s"
    cursor.execute(check_sql, (student_id, date_str))
    
    if cursor.fetchone() is None:
        # 3. INSERT
        insert_sql = "INSERT INTO attendance_log (student_id, date, time) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (student_id, date_str, time_str))
        db.commit()
        db.close()
        return True  
    else:
        db.close()
        return False 

def recognize_attendence():
    # Setup Recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()  
    recognizer.read("TrainingImageLabel" + os.sep + "Trainner.yml")
    faceCascade = cv2.CascadeClassifier("haarcascade_default.xml")
    
    # --- NEW: Load names directly from MySQL ---
    student_names = get_student_names()
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    attendance_list = [] # To save backup CSV at the end

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640) 
    cam.set(4, 480) 

    already_handled_in_session = [] 
    print("--- Attendance Session Started (Press 'q' to quit) ---")

    while True:
        ret, im = cam.read()
        if not ret: break
        
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5, minSize=(64, 64))

        for (x, y, w, h) in faces:
            Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
            match_confidence = round(100 - conf)

            # --- NEW: Lookup name from the dictionary ---
            if Id in student_names and match_confidence > 67:
                name = student_names[Id]
                ts = time.time()
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

                if Id not in already_handled_in_session:
                    status = mark_attendance_mysql(Id, date, timestamp)
                    
                    if status is True:
                        print(f"✅ Recorded: {name}")
                        attendance_list.append([Id, name, date, timestamp])
                    elif status is False:
                        messagebox.showinfo("Attendance Status", f"{name} is already marked!")
                    
                    already_handled_in_session.append(Id)
                
                color = (0, 255, 0)
                label = f"{Id}-{name} [Pass]"
            else:
                color = (0, 0, 255)
                label = "Unknown"

            cv2.rectangle(im, (x, y), (x+w, y+h), color, 2)
            cv2.putText(im, label, (x+5, y-5), font, 0.8, (255, 255, 255), 2)
            cv2.putText(im, f"{match_confidence}%", (x+5, y+h-5), font, 0.8, color, 1)

        cv2.imshow('Attendance System', im)
        if cv2.waitKey(1) == ord('q'):
            break

    # Save Session Backup
    if attendance_list:
        if not os.path.exists("Attendance"): os.makedirs("Attendance")
        df = pd.DataFrame(attendance_list, columns=['Id', 'Name', 'Date', 'Time'])
        filename = f"Attendance{os.sep}Backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"Backup saved: {filename}")

    cam.release()
    cv2.destroyAllWindows()