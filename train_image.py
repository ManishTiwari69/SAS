import os
import cv2
import numpy as np
from PIL import Image

def get_specific_images_and_labels(base_path, target_id):
    """Recursively searches through subfolders for images matching the target_id."""
    faces = []
    ids = []
    
    # os.walk loops through every subfolder inside TrainingImage
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(".jpg"):
                try:
                    parts = filename.split(".")
                    current_id = int(parts[1])
                    
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
    """
    Handles both Admin and Student training.
    Uses .update() for speed if the trainer file already exists.
    """
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # 1. Set the correct file path based on type
    folder = "TrainingImageLabel"
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    if training_type == "admin":
        trainer_path = os.path.join(folder, "AdminTrainner.yml")
    else:
        trainer_path = os.path.join(folder, "StudentTrainner.yml")

    # 2. Logic for Incremental vs Full Training
    if new_id and os.path.exists(trainer_path):
        print(f"--- Updating {training_type} Model for ID: {new_id} ---")
        recognizer.read(trainer_path)
        faces, ids = get_specific_images_and_labels("TrainingImage", new_id)
        
        if len(faces) > 0:
            # .update() keeps old data and adds new faces
            recognizer.update(faces, np.array(ids))
        else:
            print("No new images found to update.")
            return
    else:
        print(f"--- Full Training for {training_type} ---")
        # For a full train, we fetch ALL images in the folder
        imagePaths = [os.path.join("TrainingImage", f) for f in os.listdir("TrainingImage") if f.endswith(".jpg")]
        faces, ids = [], []
        
        for path in imagePaths:
            try:
                pilImage = Image.open(path).convert('L')
                faces.append(np.array(pilImage, 'uint8'))
                # Pull ID from filename
                ids.append(int(os.path.split(path)[-1].split(".")[1]))
            except Exception:
                continue
        
        if len(faces) > 0:
            recognizer.train(faces, np.array(ids))
        else:
            print("No images found to train!")
            return

    # 3. Save the specific trainer file
    recognizer.save(trainer_path)
    print(f"[SUCCESS] {training_type.capitalize()} Model Saved at {trainer_path}")