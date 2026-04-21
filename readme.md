# Attenad — AI Attendance System
AI-Powered Biometric Attendance & Admin Management System

A high-security, full-stack desktop application built with Python, OpenCV, and MySQL. This system features a dual-layer authentication process for Administrators and an automated face-recognition-based attendance logger for Students. 🚀 Key Features

Dual-File Biometric System: Separate AI models (AdminTrainner.yml and StudentTrainner.yml) to isolate login security from attendance records.

Incremental Learning: Optimized training that updates the AI model with new faces in seconds without retraining the entire dataset.

Relational Database: Structured MySQL backend with foreign key mapping between Login Credentials and Personal Profiles.

Advanced Admin Registration: Supports manual profile photo uploads or live webcam capture, including detailed metadata (DOB, Address, etc.).

Smart Attendance: Prevents duplicate marking and provides real-time confidence scores during recognition.
🛠️ Technology Stack

Language: Python 3.12

Computer Vision: OpenCV (LBPH Face Recognizer, Haar Cascades)

GUI Framework: Tkinter 

Database: MySQL (via XAMPP/phpMyAdmin)

Data Handling: Pandas, NumPy, Pillow

File Management: Shutil, OS-recursive walking
⚙️ Installation & Setup

Prerequisites
Python 3.8+ installed.
XAMPP installed (for MySQL and phpMyAdmin).
Git installed on your system.
Database Configuration

Open the XAMPP Control Panel and start the Apache and MySQL modules.

Open your browser and go to http://localhost/phpmyadmin.

Click New in the left sidebar and create a database named attendance_system.

Select the attendance_system database, click the Import tab, and upload the attendance_db (1).sql file from this repository.

Install Python Dependencies

Open your terminal, navigate to the folder where you want the project to live (but not inside an existing git project), and run:

# Clone the repository
git clone https://github.com
cd SAS

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\Activate
# On Mac/Linux:
source .venv/bin/activate

# Install required libraries
pip install -r requirement.txt bash```
pip install -r requirement.txt ```


🏃 How to Run
1. Check Database Connection. Open db_config.py and ensure your MySQL credentials are correct. Default XAMPP settings are usually:
Host: localhost
User: root
Password: "" (Empty)

2. Start the Application. Run the login script from your terminal:
#Run Python File
python login.py

3. Initial Login: Use the default administrator credentials to access the system:
Username: admin
Password: admin1234. 

4. Registration & AttendanceRegister 

Admin: Create your first biometric login profile.
Register Student: Add students to the database to enable tracking.
Mark Attendance: Click Recognize & Attendance. The system will activate the webcam, identify faces, and update the attendance_log in your MySQL database in real-time.


## RBAC Permissions

| Feature                         | Super | Teacher    |
|---                              |-------|------------|
| Dashboard                       | ✅   | ✅         |
| Check Camera                    | ✅   | ✅         |
| Recognize                       | ✅   | ✅         |
| Attendance Records              | ✅   | ✅         |
| Register Student                | ✅   | ✅         |
| Update Student                  | ✅   | ✅         |
| **Manage Students**             | ✅   | ✅         |
| **Manage Admins**               | ✅   | ❌         |
| **Register Admin**              | ✅   | ❌         |
| Edit own profile + retrain      | ✅   | ✅         |
| Edit other admins + retrain     | ✅   | ❌         |
| Change admin roles              | ✅   | ❌         |



## Directory (project root: `D:\Smart Attendance System\SAS\`)

```
SAS/
├── main.py
├── login.py
├── session.py
├── db_config.py
├── validate.py
├── train_image.py
├── edit_admin.py          
├── manage_students.py   
├── manage_admins.py       
├── admin_register.py
├── student_register.py
├── update_student.py
├── check_camera.py
├── recognize.py
├── view_attendance.py
├── capture_image.py
├── haarcascade_default.xml
├── migration.sql
├── TrainingImage/
│   ├── admin/
│   └── student/
├── TrainingImageLabel/
├── Admin_Profiles/
└── Student_Profiles/


📝 License

This project was developed as part of a BCA academic requirement.
```
