import cv2
import os
from tkinter import simpledialog, messagebox
from db_config import get_db_connection
import train_image

def register_student():
    Id = simpledialog.askstring("Input", "Enter Student ID:")
    full_name = simpledialog.askstring("Input", "Enter Full Name:")
    role = "Student" # Default role

    if Id and full_name:
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("INSERT INTO students (id, name, full_name, role) VALUES (%s, %s, %s, %s)", 
                           (int(Id), full_name.split()[0], full_name, role))
            db.commit()
            db.close()
            
            # Capture Faces
            capture_faces(Id, full_name.split()[0])
            
            # Auto-Train specifically for Students
            train_image.TrainImages(new_id=Id, training_type="student")
            messagebox.showinfo("Success", f"Student {full_name} registered!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to register: {e}")

def capture_faces(Id, name):
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier("haarcascade_default.xml")
    
    # NEW: Path: TrainingImage/student/501/
    save_path = os.path.join("TrainingImage", "student", str(Id))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    sampleNum = 0
    while True:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            sampleNum += 1
            img_name = f"{name}.{Id}.{sampleNum}.jpg"
            cv2.imwrite(os.path.join(save_path, img_name), gray[y:y+h, x:x+w])
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
        cv2.imshow('Registering Student...', img)
        if cv2.waitKey(1) & 0xFF == ord('q') or sampleNum >= 100:
            break
            
    cam.release()
    cv2.destroyAllWindows()