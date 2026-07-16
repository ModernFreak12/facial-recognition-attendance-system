import cv2
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from app.config.config import (
    WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE,
    CAM_INDEX, SHOW_FPS, WINDOW_NAME, MOBILE_CAM_URL
)

from app.detection.face_detector import FaceDetector
from app.recognition.face_recognizer import FaceRecognizer
from app.recognition.matcher import Matcher
from app.services.supabase_client import supabase

from app.utils.video import open_camera, release_camera, FPS
from app.utils.drawing import draw_label
from app.database.class_queries import start_class, end_class
from app.database.attendance_queries import mark_attendance, mark_absent_students

SMALL_FACE_THRESHOLD = 80
AUTO_SNAPSHOT_INTERVAL = 10  # 300 sec = 5 min


# -----------------------------------------------------------
# Fetch student name
# -----------------------------------------------------------
def get_student_name(student_id):
    res = (
        supabase.table("students")
        .select("name")
        .eq("student_id", student_id)
        .execute()
    )

    return res.data[0]["name"] if res.data else "Unknown"


# -----------------------------------------------------------
# Extract bbox
# -----------------------------------------------------------
def extract_bbox(det):
    if "bbox" in det:
        return det["bbox"]

    return [det["x1"], det["y1"], det["x2"], det["y2"]]


# -----------------------------------------------------------
# Prepare face
# -----------------------------------------------------------
def prepare_face(snapshot, x1, y1, x2, y2):
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
        print(f"[i] Small face ({face_w}x{face_h})")

        scale = 112 / max(face_w, face_h)
        new_w = int(crop.shape[1] * scale * 2)
        new_h = int(crop.shape[0] * scale * 2)

        crop = cv2.resize(crop, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    face = cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)

    return face


# -----------------------------------------------------------
# CLASS RUNNER
# -----------------------------------------------------------
def run_class(course_id):
    print("\n[i] Starting class...")

    # --------------------------------
    # Start class session
    # --------------------------------
    session = start_class(course_id)
    class_id = session["class_id"]
    class_start_time = datetime.now(timezone.utc)
    last_snapshot_time = time.time()

    print(f"[i] Class started: {class_id}")

    # --------------------------------
    # Load models
    # --------------------------------
    detector = FaceDetector(
        Path(WEIGHTS_PATH),
        device=DEVICE,
        conf=CONF,
        iou=IOU,
        img_size=IMG_SIZE
    )

    recognizer = FaceRecognizer(device=DEVICE)
    matcher = Matcher(course_id)

    print(f"[i] Loaded {len(matcher.student_ids)} students")

    # --------------------------------
    # Camera
    # --------------------------------
    USE_MOBILE_CAMERA = True

    if USE_MOBILE_CAMERA:
        cap = cv2.VideoCapture(MOBILE_CAM_URL)
    else:
        cap = open_camera(CAM_INDEX, width=640, height=480)

    if not cap.isOpened():
        print("[!] Could not open camera")
        return

    for _ in range(10):
        cap.read()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    fps = FPS()

    print("\n[i] Press 's' for snapshot")
    print("[i] Press 'q' to end class\n")

    # --------------------------------
    # Main loop
    # --------------------------------
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        frame = cv2.flip(frame, 1)

        if SHOW_FPS:
            fps.tick()
            cv2.putText(
                frame,
                f"FPS: {fps.value:.1f}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2
            )

        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(1) & 0xFF

        # -------------------------
        # End class
        # -------------------------
        if key == ord("q"):
            print("\n[i] Ending class...")
            mark_absent_students(class_id, course_id)
            end_class(class_id)
            break

        # -------------------------
        # Snapshot
        # -------------------------
        manual_snapshot = key == ord("s")
        auto_snapshot = time.time() - last_snapshot_time >= AUTO_SNAPSHOT_INTERVAL

        if manual_snapshot or auto_snapshot:
            snapshot = frame.copy()
            last_snapshot_time = time.time()

            if manual_snapshot:
                print("\n[i] Manual snapshot")
            else:
                print("\n[i] Automatic snapshot")

            detections = detector.predict(snapshot)
            print(f"[i] {len(detections)} face(s)")

            for det in detections:
                x1, y1, x2, y2 = extract_bbox(det)

                face = prepare_face(snapshot, int(x1), int(y1), int(x2), int(y2))

                if face is None:
                    continue

                emb = recognizer.get_embedding(face)

                if emb is None:
                    continue

                student_id, score = matcher.match(emb)

                if student_id:
                    student_name = get_student_name(student_id)
                    print(f"[MATCH] {student_name} {score:.3f}")

                    # ----------------
                    # MARK ATTENDANCE
                    # ----------------
                    mark_attendance(
                        class_id=class_id,
                        student_id=student_id,
                        class_start_time=class_start_time
                    )
                else:
                    student_name = "Unknown"

                draw_label(snapshot, (x1, y1, x2, y2), student_name)

            cv2.imshow("Recognition Result", snapshot)
            cv2.waitKey(800)

    release_camera(cap)

    print("\n[i] Class ended.")