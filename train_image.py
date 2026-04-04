import os
import cv2
import numpy as np
from PIL import Image

def get_specific_images_and_labels(base_path, target_id):
    """Recursively searches subfolders for images matching the target_id."""
    faces = []
    ids = []
    
    # We look inside TrainingImage/student/
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            # Only process face samples (exclude profile pics)
            if filename.endswith(".jpg") and not filename.startswith("profile_"):
                try:
                    # New format: sid.sample.jpg -> split(".")[0] gets the sid
                    current_id = int(filename.split(".")[0])
                    
                    if current_id == int(target_id):
                        imagePath = os.path.join(root, filename)
                        pilImage = Image.open(imagePath).convert('L')
                        imageNp = np.array(pilImage, 'uint8')
                        faces.append(imageNp)
                        ids.append(current_id)
                except (IndexError, ValueError):
                    continue
    return faces, ids

def TrainImages(new_id=None, training_type="student"):
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    label_folder = "TrainingImageLabel"
    
    if not os.path.exists(label_folder):
        os.makedirs(label_folder)
        
    trainer_path = os.path.join(label_folder, f"{training_type.capitalize()}Trainner.yml")
    
    # The base path where images are stored (TrainingImage/student)
    image_base_path = os.path.join("TrainingImage", training_type)

    if not os.path.exists(image_base_path):
        print(f"❌ {image_base_path} folder is missing!")
        return

    # Force full train if yml is missing
    if not os.path.exists(trainer_path):
        new_id = None 

    if new_id:
        # --- INCREMENTAL UPDATE ---
        print(f"--- Updating {training_type} Model for ID: {new_id} ---")
        recognizer.read(trainer_path)
        faces, ids = get_specific_images_and_labels(image_base_path, new_id)
        
        if len(faces) > 0:
            recognizer.update(faces, np.array(ids))
        else:
            print(f"No new samples found for ID {new_id} in {image_base_path}")
            return
    else:
        # --- FULL TRAINING ---
        print(f"--- Full Training for {training_type} ---")
        faces, ids = [], []
        
        for root, dirs, files in os.walk(image_base_path):
            for filename in files:
                # Ignore profile photos and hidden files
                if filename.endswith(".jpg") and not filename.startswith("profile_"):
                    try:
                        path = os.path.join(root, filename)
                        pilImage = Image.open(path).convert('L')
                        faces.append(np.array(pilImage, 'uint8'))
                        
                        # Grab ID from start of filename (e.g., "1.45.jpg" -> 1)
                        student_id = int(filename.split(".")[0])
                        ids.append(student_id)
                    except Exception:
                        continue
        
        if len(faces) > 0:
            recognizer.train(faces, np.array(ids))
        else:
            print(f"❌ No training images found in {image_base_path}")
            return

    recognizer.save(trainer_path)
    print(f"✅ {training_type.capitalize()} Model Saved at {trainer_path}")