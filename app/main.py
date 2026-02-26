import cv2
import numpy as np
from pathlib import Path

from app.config.config import (
    WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE,
    CAM_INDEX, SHOW_FPS, WINDOW_NAME,
    MOBILE_CAM_URL
)

from app.detection.face_detector import FaceDetector
from app.landmarks.landmark_detector import LandmarkDetector
from app.recognition.face_recognizer import FaceRecognizer
from app.recognition.matcher import Matcher
from app.services.supabase_client import supabase
from app.utils.video import open_camera, release_camera, FPS
from app.utils.drawing import draw_label


# -----------------------------------------------------------
# Thresholds
# -----------------------------------------------------------
SMALL_FACE_THRESHOLD = 80   # px — bounding box width or height below this = "distant face"


# -----------------------------------------------------------
# Fetch student name from DB
# -----------------------------------------------------------
def get_student_name(student_id: str):
    res = (
        supabase.table("students")
        .select("name")
        .eq("student_id", student_id)
        .execute()
    )
    return res.data[0]["name"] if res.data else "Unknown"


# -----------------------------------------------------------
# Extract bbox from detection dict
# -----------------------------------------------------------
def extract_bbox(det):
    if "bbox" in det:
        return det["bbox"]
    return [det["x1"], det["y1"], det["x2"], det["y2"]]


# -----------------------------------------------------------
# Prepare face crop for embedding
# Handles both close and distant faces
# -----------------------------------------------------------
def prepare_face(snapshot: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """
    Crops the detected face with padding, then:
    - If face is small (distant) → upscale using bicubic before resizing to 112x112
    - If face is normal size    → direct resize to 112x112
    """
    pad = 20
    x1p = int(max(0, x1 - pad))
    y1p = int(max(0, y1 - pad))
    x2p = int(min(snapshot.shape[1], x2 + pad))
    y2p = int(min(snapshot.shape[0], y2 + pad))

    crop = snapshot[y1p:y2p, x1p:x2p]
    if crop.size == 0:
        return None

    face_w = x2 - x1
    face_h = y2 - y1

    if face_w < SMALL_FACE_THRESHOLD or face_h < SMALL_FACE_THRESHOLD:
        # Distant face — upscale first to recover some detail
        print(f"[i] Small face detected ({face_w}x{face_h}px) — applying upscale")
        scale  = 112 / max(face_w, face_h)
        new_w  = int(crop.shape[1] * scale * 2)   # 2x extra then we'll resize down
        new_h  = int(crop.shape[0] * scale * 2)
        crop   = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    else:
        print(f"[i] Normal face ({face_w}x{face_h}px) — direct resize")

    # Final resize to model input
    face = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)
    return face


# -----------------------------------------------------------
# MAIN APPLICATION (SNAPSHOT MODE)
# -----------------------------------------------------------
def main():
    print(f"[i] Loading YOLO detection model: {Path(WEIGHTS_PATH).resolve()}")
    detector = FaceDetector(Path(WEIGHTS_PATH), device=DEVICE, conf=CONF, iou=IOU, img_size=IMG_SIZE)

    print("[i] Loading landmark model ...")
    landm = LandmarkDetector()   # kept for future use

    print("[i] Loading ArcFace embedding model...")
    recognizer = FaceRecognizer(device=DEVICE)

    print("[i] Loading stored embeddings from database...")
    matcher = Matcher()
    print(f"[i] Loaded {len(matcher.student_ids)} embedding rows.\n")

    # -------------------------------------------------------
    # Open camera
    # -------------------------------------------------------
    USE_MOBILE_CAMERA = True

    if USE_MOBILE_CAMERA:
        print("[i] Using mobile camera:", MOBILE_CAM_URL)
        cap = cv2.VideoCapture(MOBILE_CAM_URL)
    else:
        cap = open_camera(CAM_INDEX, width=640, height=480)

    if not cap.isOpened():
        print("[!] ERROR: Could not open camera stream.")
        return

    # Warm-up
    for _ in range(10):
        cap.read()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    fps = FPS()

    print("[i] Snapshot recognition ready — Press 's' to detect, 'q' to quit.\n")

    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("[!] Failed to read frame. Retrying...")
            continue

        frame = cv2.flip(frame, 1)

        if SHOW_FPS:
            fps.tick()
            cv2.putText(frame, f"FPS: {fps.value:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        # ---------------------------------------------------
        # SNAPSHOT — run full pipeline on 's'
        # ---------------------------------------------------
        if key == ord("s"):
            snapshot = frame.copy()
            print("\n[i] Snapshot captured — running face recognition...")

            detections = detector.predict(snapshot)
            print(f"[i] Detected {len(detections)} face(s).")

            for det in detections:
                x1, y1, x2, y2 = extract_bbox(det)

                face = prepare_face(snapshot, int(x1), int(y1), int(x2), int(y2))
                if face is None:
                    print("[!] Skipping: empty crop")
                    continue

                emb = recognizer.get_embedding(face)
                if emb is None:
                    print("[!] Skipping: embedding failed")
                    continue

                # Match — aggregates across all augmented embeddings per student
                student_id, score = matcher.match(emb)

                if student_id:
                    student_name = get_student_name(student_id)
                    print(f"[MATCH] {student_name} ({student_id}) — score={score:.3f}")
                else:
                    student_name = "Unknown"
                    print(f"[NO MATCH] score={score:.3f}")

                draw_label(snapshot, (x1, y1, x2, y2), student_name)

            cv2.imshow("Recognition Result", snapshot)
            cv2.waitKey(800)

    release_camera(cap)
    print("[i] Camera released — Exit clean.\n")


if __name__ == "__main__":
    main()