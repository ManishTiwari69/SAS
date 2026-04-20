"""
train_image.py  —  Face model training / incremental update.

Storage layout
──────────────
  Admin   images  →  TrainingImage/admin/{admin_id}/{admin_id}.{n}.jpg
  Student images  →  TrainingImage/student/{student_id}/{student_id}.{n}.jpg

Trainer files
─────────────
  TrainingImageLabel/AdminTrainner.yml
  TrainingImageLabel/StudentTrainner.yml
"""

import os
import cv2
import numpy as np
from PIL import Image

# ── Project root (same directory as this script) ──────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
LABEL_DIR      = os.path.join(BASE_DIR, "TrainingImageLabel")
TRAINING_DIR   = os.path.join(BASE_DIR, "TrainingImage")


def _trainer_path(training_type: str) -> str:
    os.makedirs(LABEL_DIR, exist_ok=True)
    return os.path.join(LABEL_DIR, f"{training_type.capitalize()}Trainner.yml")


def _image_base(training_type: str) -> str:
    return os.path.join(TRAINING_DIR, training_type)


# ── Image + label collectors ──────────────────────────────────────────

def _collect_for_id(base_path: str, target_id: int):
    """Return (faces, ids) for a single person's images only."""
    faces, ids = [], []
    for root, _, files in os.walk(base_path):
        for fname in files:
            if not fname.endswith(".jpg") or fname.startswith("profile_"):
                continue
            try:
                file_id = int(fname.split(".")[0])
                if file_id != target_id:
                    continue
                img_path = os.path.join(root, fname)
                pil_img  = Image.open(img_path).convert("L")
                faces.append(np.array(pil_img, "uint8"))
                ids.append(file_id)
            except (ValueError, IndexError):
                continue
    return faces, ids


def _collect_all(base_path: str):
    """Return (faces, ids) for every person under base_path."""
    faces, ids = [], []
    for root, _, files in os.walk(base_path):
        for fname in files:
            if not fname.endswith(".jpg") or fname.startswith("profile_"):
                continue
            try:
                file_id  = int(fname.split(".")[0])
                img_path = os.path.join(root, fname)
                pil_img  = Image.open(img_path).convert("L")
                faces.append(np.array(pil_img, "uint8"))
                ids.append(file_id)
            except (ValueError, IndexError):
                continue
    return faces, ids


# ── Public API ────────────────────────────────────────────────────────

def TrainImages(new_id=None, training_type="student"):
    """
    Parameters
    ----------
    new_id        : int | None
        When given, do an *incremental* update for that single person.
        When None, do a *full* retrain from scratch.
    training_type : 'student' | 'admin'
    """
    recognizer  = cv2.face.LBPHFaceRecognizer_create()
    trainer_pth = _trainer_path(training_type)
    image_base  = _image_base(training_type)

    if not os.path.exists(image_base):
        print(f"❌  Image folder missing: {image_base}")
        return False

    # Force full retrain if the YML doesn't exist yet
    if not os.path.exists(trainer_pth):
        new_id = None

    if new_id is not None:
        # ── INCREMENTAL ────────────────────────────────────────────────
        print(f"[train_image] Incremental update for {training_type} ID={new_id}")
        recognizer.read(trainer_pth)
        faces, ids = _collect_for_id(image_base, int(new_id))
        if not faces:
            print(f"[train_image] No samples found for ID {new_id}")
            return False
        recognizer.update(faces, np.array(ids))
    else:
        # ── FULL RETRAIN ───────────────────────────────────────────────
        print(f"[train_image] Full retrain for {training_type}")
        faces, ids = _collect_all(image_base)
        if not faces:
            print(f"[train_image] No training images in {image_base}")
            return False
        recognizer.train(faces, np.array(ids))

    recognizer.save(trainer_pth)
    print(f"[train_image] ✅  Model saved → {trainer_pth}")
    return True
