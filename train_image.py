import os
import cv2
import numpy as np
from PIL import Image

def get_specific_images_and_labels(path, target_id):
    """Only fetches images belonging to the NEWLY registered ID."""
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    ids = []
    
    for imagePath in imagePaths:
        # Expected format: Name.ID.SampleNum.jpg
        filename = os.path.split(imagePath)[-1]
        try:
            current_id = int(filename.split(".")[1])
            # Only process if it matches the ID we just captured
            if current_id == int(target_id):
                pilImage = Image.open(imagePath).convert('L')
                imageNp = np.array(pilImage, 'uint8')
                faces.append(imageNp)
                ids.append(current_id)
        except (IndexError, ValueError):
            continue
            
    return faces, ids

def TrainImages(new_id=None):
    """
    If new_id is provided, it performs Incremental Training (Fast).
    If new_id is None, it performs Full Training (Slow).
    """
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    trainer_path = "TrainingImageLabel" + os.sep + "Trainner.yml"
    
    # Ensure directory exists
    if not os.path.exists("TrainingImageLabel"):
        os.makedirs("TrainingImageLabel")

    # 1. Check if we are UPDATING or STARTING FRESH
    if new_id and os.path.exists(trainer_path):
        print(f"--- Incremental Training for ID: {new_id} ---")
        recognizer.read(trainer_path)
        faces, ids = get_specific_images_and_labels("TrainingImage", new_id)
        
        if len(faces) > 0:
            # .update() adds to the existing model instead of overwriting it
            recognizer.update(faces, np.array(ids))
            print(f"Successfully updated model with {len(faces)} new images.")
        else:
            print("No new images found for this ID.")
            return
    else:
        print("--- Full System Training ---")
        # Fallback to your old method for the very first time
        from capture_image import is_number # using utility to fetch all
        imagePaths = [os.path.join("TrainingImage", f) for f in os.listdir("TrainingImage")]
        faces, ids = [], []
        for path in imagePaths:
            pilImage = Image.open(path).convert('L')
            faces.append(np.array(pilImage, 'uint8'))
            ids.append(int(os.path.split(path)[-1].split(".")[1]))
        
        recognizer.train(faces, np.array(ids))

    # 2. Save the result
    recognizer.save(trainer_path)
    print("[SUCCESS] AI Model Synchronized.")