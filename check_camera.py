import cv2
import tkinter as tk
from PIL import Image, ImageTk

def camer(container):
    # 1. Clear the dashboard content area
    for widget in container.winfo_children():
        widget.destroy()

    # 2. UI Setup
    header = tk.Frame(container, bg="#1a1c23", height=50)
    header.pack(side="top", fill="x")
    tk.Label(header, text="📷 CAMERA SYSTEM CHECK", font=("Arial", 14, "bold"), 
             bg="#1a1c23", fg="#00d084").pack(pady=10)

    # Label where the video will actually show
    video_display = tk.Label(container, bg="black")
    video_display.pack(pady=20, padx=20)

    # 3. Camera Setup
    # Use a list for 'cap' so it's accessible inside the nested function
    cap = [cv2.VideoCapture(0)]
    face_cascade = cv2.CascadeClassifier("haarcascade_default.xml")

    def update_frame():
        if not cap[0] or not cap[0].isOpened():
            return

        ret, frame = cap[0].read()
        if ret:
            # Mirror the frame for a more natural feel
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 208, 132), 2)

            # Convert OpenCV BGR to RGB for PIL
            cv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_img).resize((700, 500), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update the label
            video_display.imgtk = imgtk
            video_display.configure(image=imgtk)

            # Schedule the next update in 10ms (This replaces 'while True')
            video_display.after(10, update_frame)

    # 4. Cleanup Function
    def stop_camera():
        if cap[0]:
            cap[0].release()
            cap[0] = None
        # Go back to the dashboard overview
        import main
        main.render_dashboard(container.winfo_toplevel())

    # Stop Button
    tk.Button(container, text="❌ Close Camera", command=stop_camera, 
              bg="#e74c3c", fg="white", font=("Arial", 11, "bold"), width=20).pack(pady=10)

    # Start the loop
    update_frame()