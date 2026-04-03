import csv
import cv2
import os
from db_config import get_db_connection
from tkinter import simpledialog, messagebox

def is_student_registered(Id):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        sql = "SELECT * FROM students WHERE id = %s"
        cursor.execute(sql, (int(Id),))
        return cursor.fetchone() is not None
    finally:
        db.close()

def check_for_duplicate_face():
    """Returns the ID of the person if their face is already recognized."""
    trainer_path = "TrainingImageLabel" + os.sep + "Trainner.yml"
    if not os.path.exists(trainer_path):
        return None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(trainer_path)
    detector = cv2.CascadeClassifier("haarcascade_default.xml")
    
    cap = cv2.VideoCapture(0)
    found_id = None
    
    # Scan for 2 seconds (roughly 40-60 frames)
    for _ in range(50):
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            # lower confidence score in LBPH means better match
            predicted_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            if confidence < 50:  # Adjust threshold for strictness
                found_id = predicted_id
                break
        if found_id: break
        
    cap.release()
    cv2.destroyAllWindows()
    return found_id

def is_number(s):
    """Utility function to check if the input ID is a valid number."""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

def save_student_to_mysql(Id, name):
    """Saves the newly registered student to the MySQL 'students' table."""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        # Using %s to prevent SQL injection
        sql = "INSERT INTO students (id, name) VALUES (%s, %s)"
        cursor.execute(sql, (int(Id), name))
        db.commit()
        db.close()
        print(f"✅ Student {name} (ID: {Id}) saved to MySQL database.")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        messagebox.showerror("DB Error", f"Could not save student to database: {e}")

        
def takeImages():
    # ... the rest of your takeImages code follows here ...
    Id = simpledialog.askstring("Input", "Enter Your Id:")
    name = simpledialog.askstring("Input", "Enter Your Name:")

    # Now this line will work because is_number is defined above!
    if Id and name and is_number(Id) and name.isalpha():
        
        # 1. Check if ID exists in MySQL
        if is_student_registered(Id):
            messagebox.showwarning("Error", f"ID {Id} is already in use.")
            return

        # 2. Check if Face is already recognized under a different ID
        print("Scanning for existing registration...")
        existing_id = check_for_duplicate_face()
        if existing_id:
            messagebox.showerror("Duplicate Detected", 
                                 f"This person is already registered with ID: {existing_id}\n"
                                 "You cannot create a second entry for the same person.")
            return

        # 3. Proceed with image capture
        cam = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier("haarcascade_default.xml")
        sampleNum = 0
        if not os.path.exists("TrainingImage"): os.makedirs("TrainingImage")

        while True:
            ret, img = cam.read()
            if not ret: break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)
            
            for(x,y,w,h) in faces:
                cv2.rectangle(img, (x, y), (x+w, y+h), (10, 159, 255), 2)
                sampleNum += 1
                img_path = f"TrainingImage{os.sep}{name}.{Id}.{sampleNum}.jpg"
                cv2.imwrite(img_path, gray[y:y+h, x:x+w])
                cv2.imshow('Face Capture', img)
            
            if cv2.waitKey(1) & 0xFF == ord('q') or sampleNum >= 100:
                break
                
        cam.release()
        cv2.destroyAllWindows()
        
        # Save to Database and CSV
        save_student_to_mysql(Id, name)
        save_to_csv_backup(Id, name)
        
        messagebox.showinfo("Success", f"Registration complete for {name}")
        
        # CRITICAL: Return the Id so main.py can start training
        return Id 

    else:
        messagebox.showerror("Error", "Invalid Input. Use numbers for ID and letters for Name.")
        return None

def save_to_csv_backup(Id, name):
    if not os.path.exists("StudentDetails"): os.makedirs("StudentDetails")
    file_path = "StudentDetails" + os.sep + "StudentDetails.csv"
    exists = os.path.isfile(file_path)
    with open(file_path, 'a+', newline='') as f:
        writer = csv.writer(f)
        if not exists or os.stat(file_path).st_size == 0:
            writer.writerow(["Id", "Name"])
        writer.writerow([Id, name])