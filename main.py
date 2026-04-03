import tkinter as tk
from tkinter import messagebox
import os
import check_camera
import capture_image
import train_image
import recognize
import view_attendance 

def launch_dashboard():
    # Move ALL your GUI code (window = tk.Tk(), buttons, title, etc.) here
    window = tk.Tk()
    # ... everything else ...
    window.mainloop()

if __name__ == "__main__":
    # If someone tries to run main.py directly, redirect them to login
    import login
    login.login_page()

def check_cam():
    check_camera.camer()

def capture_and_train():
    # 1. Capture and get the ID back from the function
    # (Note: You'll need to make takeImages return the ID)
    new_id = capture_image.takeImages() 
    
    if new_id:
        print(f"Starting optimized training for ID: {new_id}")
        train_image.TrainImages(new_id=new_id)
        messagebox.showinfo("Success", f"Student {new_id} Registered and Model Updated!")

def recognize_attendance():
    recognize.recognize_attendence()

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        window.destroy()

# --- GUI Setup ---
window = tk.Tk()
window.title("Face Recognition Attendance System")
window.geometry("600x500")
window.configure(background='#2c3e50') 

# Title Label
title = tk.Label(window, text="ATTENDANCE SYSTEM", 
                 bg="#2c3e50", fg="white", 
                 font=('times', 30, 'bold'))
title.pack(pady=30)

# --- Buttons ---
btn_style = {
    "font": ('times', 15, 'bold'),
    "bg": "#3498db",
    "fg": "white",
    "width": 30,
    "height": 2,
    "activebackground": "#2980b9"
}

# Button 1: Check Camera
btn1 = tk.Button(window, text="1. Check Camera", command=check_cam, **btn_style)
btn1.pack(pady=10)

# Button 2: Now handles BOTH Capture and Training
btn2 = tk.Button(window, text="2. Register New Student", command=capture_and_train, **btn_style)
btn2.pack(pady=10)

# Button 3: Recognition
btn4 = tk.Button(window, text="3. Recognize & Attendance", command=recognize_attendance, **btn_style)
btn4.pack(pady=10)

btn_view = tk.Button(window, text="4. View Attendance Report", 
                     command=view_attendance.show_attendance, **btn_style)
btn_view.pack(pady=10)
# Button 4: Quit
btn5 = tk.Button(window, text="Quit", command=on_closing, 
                 font=('times', 15, 'bold'), bg="#e74c3c", fg="white", 
                 width=30, height=2)
btn5.pack(pady=10)

# Run the GUI
window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()