import cv2
import numpy as np
import uuid
from pathlib import Path
from datetime import datetime

# --- Project Imports ---
from app.services.supabase_client import supabase
from app.config.config import (
    WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE,
    CAM_INDEX, SHOW_FPS, WINDOW_NAME,
    MOBILE_CAM_URL
)
from app.detection.face_detector import FaceDetector
from app.landmarks.landmark_detector import LandmarkDetector
from app.utils.alignment import align_face
from app.recognition.face_recognizer import FaceRecognizer


# ------------------------------------------------------------
#   USER INPUT → USE UNIVERSITY ROLL NUMBER
# ------------------------------------------------------------
UNIV_ROLL_NO = "12200222047"      # <-- CHANGE THIS
NUM_EMBEDDINGS = 3


# ------------------------------------------------------------
#   HELPERS
# ------------------------------------------------------------
def get_student_uuid(univ_roll_no: str):
    """Fetch student_id (UUID) by univ_roll_no."""
    res = (
        supabase.table("students")
        .select("student_id")
        .eq("univ_roll_no", univ_roll_no)
        .execute()
    )

    data = res.data
    if not data:
        print(f"❌ No student found with univ_roll_no = {univ_roll_no}")
        return None

    return data[0]["student_id"]


def register_single_embedding(frame, detector, landm, recognizer):
    """Detect → Landmark → Align → Embed"""
    detections = detector.predict(frame)
    if not detections:
        print("No face detected.")
        return None

    det = detections[0]  # first detected face
    x1, y1, x2, y2 = map(int, [det["x1"], det["y1"], det["x2"], det["y2"]])

    face_crop = frame[y1:y2, x1:x2]
    if face_crop.size == 0:
        print("Bad crop.")
        return None

    lm = landm.predict(face_crop)
    if lm is None:
        print("No landmarks detected.")
        return None

    aligned = align_face(face_crop, lm)
    if aligned is None:
        print("Alignment failed.")
        return None

    emb = recognizer.get_embedding(aligned)
    if emb is None:
        print("Embedding failed.")
        return None

    return emb.tolist()


def save_embedding_to_supabase(student_uuid, embedding):
    row = {
        "embedding_id": str(uuid.uuid4()),
        "student_id": student_uuid,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat(),
    }

    supabase.table("student_embeddings").insert(row).execute()
    print("✔ Saved embedding.")


# ------------------------------------------------------------
#   MAIN REGISTRATION LOOP
# ------------------------------------------------------------
def main():
    print("\n=== Student Face Registration ===")
    print("Using univ_roll_no:", UNIV_ROLL_NO)

    student_uuid = get_student_uuid(UNIV_ROLL_NO)
    if student_uuid is None:
        print("Registration aborted.")
        return

    print("Resolved student_id:", student_uuid)

    # Load modules
    detector = FaceDetector(Path(WEIGHTS_PATH), device=DEVICE, conf=CONF, iou=IOU, img_size=IMG_SIZE)
    
    landm = LandmarkDetector(device=DEVICE)
    recognizer = FaceRecognizer(device=DEVICE)

    # --------------------------------------------------------
    #   USE MOBILE CAMERA (same as main.py)
    # --------------------------------------------------------
    USE_MOBILE_CAMERA = True

    if USE_MOBILE_CAMERA:
        print("\n[i] Using mobile camera stream:", MOBILE_CAM_URL)
        cap = cv2.VideoCapture(MOBILE_CAM_URL)
    else:
        print("\n[i] Using default laptop webcam")
        cap = cv2.VideoCapture(0)

    collected = 0

    print("\nPress SPACE to capture an embedding.")
    print("Press Q to quit.\n")

    while collected < NUM_EMBEDDINGS:
        ret, frame = cap.read()
        if not ret:
            print("[!] Camera read failed.")
            break

        frame = cv2.flip(frame, 1)

        cv2.imshow("Register Student", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == ord(" "):
            print(f"\nCapturing embedding {collected + 1}/{NUM_EMBEDDINGS}")
            emb = register_single_embedding(frame, detector, landm, recognizer)

            if emb:
                save_embedding_to_supabase(student_uuid, emb)
                collected += 1

    cap.release()
    cv2.destroyAllWindows()
    print("\n✔ Registration Completed.\n")


if __name__ == "__main__":
    main()