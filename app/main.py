import cv2
from pathlib import Path

from app.config.config import (
    WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE,
    CAM_INDEX, SHOW_FPS, WINDOW_NAME,
    MOBILE_CAM_URL
)

from app.detection.face_detector import FaceDetector
from app.landmarks.landmark_detector import LandmarkDetector
from app.utils.alignment import align_face
from app.recognition.face_recognizer import FaceRecognizer
from app.recognition.matcher import Matcher
from app.services.supabase_client import supabase
from app.utils.video import open_camera, release_camera, FPS
from app.utils.drawing import draw_label


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
# MAIN APPLICATION (SNAPSHOT MODE)
# -----------------------------------------------------------
def main():
    print(f"[i] Loading YOLO detection model: {Path(WEIGHTS_PATH).resolve()}")
    detector = FaceDetector(Path(WEIGHTS_PATH), device=DEVICE, conf=CONF, iou=IOU, img_size=IMG_SIZE)

    print("[i] Loading landmark model ...")
    landm = LandmarkDetector()

    print("[i] Loading ArcFace embedding model...")
    recognizer = FaceRecognizer(device=DEVICE)

    print("[i] Loading stored embeddings from database...")
    matcher = Matcher()
    print(f"[i] Loaded {len(matcher.student_ids)} student embeddings.\n")

    # -------------------------------------------------------
    # Open camera AFTER model load (important)
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

    # Warm-up frames for mobile MJPEG streams
    for _ in range(10):
        cap.read()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    fps = FPS()

    print("[i] Snapshot recognition ready — Press 's' to detect, 'q' to quit.\n")

    # -------------------------------------------------------
    # MAIN LOOP (NO YOLO HERE)
    # -------------------------------------------------------
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("[!] Failed to read frame. Retrying...")
            continue

        frame = cv2.flip(frame, 1)

        # Display FPS
        if SHOW_FPS:
            fps.tick()
            cv2.putText(frame, f"FPS: {fps.value:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF

        # Quit
        if key == ord("q"):
            break

        # ---------------------------------------------------
        # SNAPSHOT MODE — Only run full pipeline on 's'
        # ---------------------------------------------------
        if key == ord("s"):
            snapshot = frame.copy()
            print("\n[i] Snapshot captured — running face recognition...")

            detections = detector.predict(snapshot)
            print(f"[i] Detected {len(detections)} face(s).")

            for det in detections:
                x1, y1, x2, y2 = extract_bbox(det)
                pad = 40  # increased from whatever it is now
                x1p = int(max(0, x1 - pad))
                y1p = int(max(0, y1 - pad))
                x2p = int(min(snapshot.shape[1], x2 + pad))
                y2p = int(min(snapshot.shape[0], y2 + pad))

                crop = snapshot[y1p:y2p, x1p:x2p]
                
                if crop.size == 0:
                    print("[!] Skipping: empty crop")
                    continue

                '''
                lm = landm.predict(crop)
                if lm is None:
                    print("[!] Skipping: no landmarks found")
                    continue

                aligned = align_face(crop, lm)
                if aligned is None:
                    print("[!] Skipping: alignment failed")
                    continue
                        # In main.py, after aligned = align_face(crop, lm)
                import os
                debug_dir = "debug_faces"
                os.makedirs(debug_dir, exist_ok=True)

                # Save crop before alignment
                cv2.imwrite(f"{debug_dir}/crop.png", crop)

                # Draw landmarks on crop
                crop_lm = crop.copy()
                for (x, y) in lm:
                    cv2.circle(crop_lm, (int(x), int(y)), 3, (0, 255, 0), -1)
                cv2.imwrite(f"{debug_dir}/crop_with_landmarks.png", crop_lm)

                # Save aligned
                cv2.imwrite(f"{debug_dir}/aligned.png", aligned)

                print(f"[DEBUG] Saved debug images to {debug_dir}/")
                '''

                aligned = cv2.resize(crop, (112, 112))

                emb = recognizer.get_embedding(aligned)
                if emb is None:
                    print("[!] Skipping: no embedding")
                    continue


                    # -----------------------------------------------
                # DEBUG — Print similarity scores for all students
                # -----------------------------------------------
                from numpy.linalg import norm
                import numpy as np

                emb_normalized = emb / norm(emb)

                if matcher.embeddings.size > 0:
                    sims = matcher.embeddings @ emb_normalized
                    print("\n[DEBUG] Similarity scores:")
                    for sid, sim in zip(matcher.student_ids, sims):
                        print(f"         {sid} → {sim:.4f}")
                    print(f"         Best score : {float(np.max(sims)):.4f}")
                    print(f"         Threshold  : 0.70")
                    print()

    
                # Match
                student_id, score = matcher.match(emb)

                if student_id:
                    student_name = get_student_name(student_id)
                    print(f"[MATCH] {student_name} ({student_id}) — score={score:.3f}")
                else:
                    student_name = "Unknown"
                    print(f"[NO MATCH] score={score:.3f}")

                # Draw on snapshot
                draw_label(snapshot, (x1, y1, x2, y2), student_name)

            # Show result for a moment
            cv2.imshow("Recognition Result", snapshot)
            cv2.waitKey(800)


    # Cleanup
    release_camera(cap)
    print("[i] Camera released — Exit clean.\n")


if __name__ == "__main__":
    main()