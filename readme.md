AI-Powered Biometric Attendance & Admin Management System

A high-security, full-stack desktop application built with Python, OpenCV, and MySQL. This system features a dual-layer authentication process for Administrators and an automated face-recognition-based attendance logger for Students.
🚀 Key Features

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
1. Prerequisites
* **Python 3.8+** installed.
* **XAMPP** installed (for MySQL and phpMyAdmin).
* **Git** installed on your system.

2. Database Configuration
1. Open the **XAMPP Control Panel** and start the **Apache** and **MySQL** modules.
2. Open your browser and go to [http://localhost/phpmyadmin](http://localhost/phpmyadmin).
3. Click **New** in the left sidebar and create a database named `attendance_system`.
4. Select the `attendance_system` database, click the **Import** tab, and upload the `attendance_db (1).sql` file from this repository.

3. Install Python Dependencies

Open your terminal, navigate to the folder where you want the project to live (but not inside an existing git project), and run:

```bash
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

📂 Project Structure
Plaintext

├── TrainingImage/            # Structured: /admin/[ID] and /student/[ID]
├── TrainingImageLabel/       # Stores generated .yml AI models
├── Attendance/               # CSV Backup logs
├── db_config.py              # MySQL connection settings
├── login.py                  # Entry point (Authentication)
├── main.py                   # Admin Dashboard
├── admin_register.py         # Profile & Biometric logic
├── student_register.py       # Student enrollment logic
├── train_image.py            # Incremental AI training logic
└── recognize.py              # Real-time recognition engine

📝 License

This project was developed as part of a BCA academic requirement.
