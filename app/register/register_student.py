import cv2
import numpy as np
import uuid
from pathlib import Path
from datetime import datetime

# --- Project Imports ---
from app.services.supabase_client import supabase
from app.config.config import (
    WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE,
    MOBILE_CAM_URL, USE_MOBILE_CAMERA
)
from app.detection.face_detector import FaceDetector
from app.recognition.face_recognizer import FaceRecognizer


# ------------------------------------------------------------
#   CONFIG
# ------------------------------------------------------------
UNIV_ROLL_NO   = "12200222032"    # <-- CHANGE THIS
NUM_CAPTURES   = 1              


# ------------------------------------------------------------
#   AUGMENTATION PIPELINE
#
#   Categories covered:
#     A. Original
#     B. Distance simulation      (downscale → upscale)
#     C. Blur / focus             (Gaussian blur)
#     D. Lighting — bright/dark   (global brightness shift)
#     E. Lighting — contrast      (CLAHE, gamma)
#     F. Lighting — shadows       (gradient shadow overlay)
#     G. Pose — in-plane rotation (warpAffine)
#     H. Pose — horizontal flip
#     I. Partial occlusion        (rectangular mask regions)
#     J. Noise                    (Gaussian)
#     K. Combined scenarios       (distance + lighting)
#
#   Stored in DB: 1 mean embedding per student
# ------------------------------------------------------------

def _rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def _adjust_brightness(img: np.ndarray, delta: int) -> np.ndarray:
    return np.clip(img.astype(np.int32) + delta, 0, 255).astype(np.uint8)


def _adjust_gamma(img: np.ndarray, gamma: float) -> np.ndarray:
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in range(256)], dtype=np.uint8)
    return cv2.LUT(img, table)


def _add_noise(img: np.ndarray, std: float = 12.0) -> np.ndarray:
    noise = np.random.normal(0, std, img.shape).astype(np.int32)
    return np.clip(img.astype(np.int32) + noise, 0, 255).astype(np.uint8)


def _downscale_upscale(img: np.ndarray, scale: float) -> np.ndarray:
    """Simulate distance — compress then restore to 112x112."""
    h, w = img.shape[:2]
    sw = max(8, int(w * scale))
    sh = max(8, int(h * scale))
    small = cv2.resize(img, (sw, sh), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)


def _add_shadow(img: np.ndarray, direction: str = "left") -> np.ndarray:
    """Simulate partial lighting shadow from one side."""
    h, w = img.shape[:2]
    gradient = np.linspace(0.35, 1.0, w) if direction == "left" else np.linspace(1.0, 0.35, w)
    gradient = gradient[np.newaxis, :, np.newaxis]
    return np.clip(img.astype(np.float32) * gradient, 0, 255).astype(np.uint8)


def _occlude(img: np.ndarray, region: str) -> np.ndarray:
    """
    Simulate partial face occlusion:
      lower  → mask/scarf/desk blocking lower face
      upper  → cap/hair blocking forehead
      left   → person/object partially blocking left side
      right  → person/object partially blocking right side
    """
    out = img.copy()
    h, w = out.shape[:2]
    if region == "lower":
        out[h // 2:, :] = 128
    elif region == "upper":
        out[:h // 3, :] = 128
    elif region == "left":
        out[:, :w // 3] = 128
    elif region == "right":
        out[:, 2 * w // 3:] = 128
    return out


def _clahe(img: np.ndarray) -> np.ndarray:
    """Contrast Limited Adaptive Histogram Equalization."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def augment_face(face_crop: np.ndarray) -> list:
    """
    Takes a clean 112x112 face crop.
    Returns a list of ~30 augmented np.ndarray images.
    """
    f = face_crop
    v = []

    # A. Original
    v.append(f.copy())                                                      # 1

    # B. Distance simulation
    v.append(_downscale_upscale(f, 0.5))                                    # 2  mild
    v.append(_downscale_upscale(f, 0.25))                                   # 3  moderate
    v.append(_downscale_upscale(f, 0.15))                                   # 4  far

    # C. Blur
    v.append(cv2.GaussianBlur(f, (3, 3), 0))                               # 5  mild
    v.append(cv2.GaussianBlur(f, (5, 5), 0))                               # 6  medium
    v.append(cv2.GaussianBlur(f, (7, 7), 0))                               # 7  heavy

    # D. Brightness
    v.append(_adjust_brightness(f, +50))                                    # 8  bright
    v.append(_adjust_brightness(f, -50))                                    # 9  dark
    v.append(_adjust_brightness(f, +90))                                    # 10 window glare
    v.append(_adjust_brightness(f, -90))                                    # 11 back of room

    # E. Gamma / contrast
    v.append(_adjust_gamma(f, 1.8))                                         # 12 high gamma
    v.append(_adjust_gamma(f, 0.55))                                            # 13 low gamma
    v.append(_clahe(f))                                                     # 14 CLAHE

    # F. Shadow
    v.append(_add_shadow(f, "left"))                                        # 15
    v.append(_add_shadow(f, "right"))                                       # 16

    # G. In-plane rotation (head tilt)
    v.append(_rotate(f,  10))                                               # 17
    v.append(_rotate(f, -10))                                               # 18
    v.append(_rotate(f,  20))                                               # 19
    v.append(_rotate(f, -20))                                               # 20

    # H. Horizontal flip (mild pose change)
    v.append(cv2.flip(f, 1))                                                # 21

    # I. Occlusion
    v.append(_occlude(f, "lower"))                                          # 22 mask/scarf
    v.append(_occlude(f, "upper"))                                          # 23 cap/hair
    v.append(_occlude(f, "left"))                                           # 24
    v.append(_occlude(f, "right"))                                          # 25

    # J. Noise
    v.append(_add_noise(f, std=10))                                         # 26
    v.append(_add_noise(f, std=22))                                         # 27

    # K. Combined scenarios
    v.append(_adjust_brightness(_downscale_upscale(f, 0.5), +40))          # 28 far + bright
    v.append(_adjust_brightness(_downscale_upscale(f, 0.5), -40))          # 29 far + dark
    v.append(cv2.GaussianBlur(_downscale_upscale(f, 0.4), (3, 3), 0))     # 30 far + blur

    return v  # 30 total


# ------------------------------------------------------------
#   HELPERS
# ------------------------------------------------------------
def get_student_uuid(univ_roll_no: str):
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


def extract_face_crop(frame: np.ndarray, detector) -> np.ndarray | None:
    """Detect face → clean 112x112 crop."""
    detections = detector.predict(frame)
    if not detections:
        print("  [!] No face detected.")
        return None

    det = detections[0]
    x1, y1, x2, y2 = map(int, [det["x1"], det["y1"], det["x2"], det["y2"]])

    pad = 10
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(frame.shape[1], x2 + pad)
    y2 = min(frame.shape[0], y2 + pad)

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        print("  [!] Bad crop.")
        return None

    return cv2.resize(crop, (112, 112), interpolation=cv2.INTER_CUBIC)


def compute_mean_embedding(all_embeddings: list) -> np.ndarray | None:
    """
    Average all embeddings then re-normalize.
    Produces one robust vector covering all conditions.
    """
    stacked = np.array(all_embeddings, dtype=np.float32)   # (N, 512)
    mean    = np.mean(stacked, axis=0)                      # (512,)
    n       = np.linalg.norm(mean)
    if n == 0:
        return None
    return (mean / n).astype(np.float32)


def delete_existing_embeddings(student_uuid: str):
    (
        supabase.table("student_embeddings")
        .delete()
        .eq("student_id", student_uuid)
        .execute()
    )
    print("  ✔ Old embeddings deleted.")


def save_mean_embedding(student_uuid: str, embedding: np.ndarray):
    row = {
        "embedding_id": str(uuid.uuid4()),
        "student_id": student_uuid,
        "embedding": embedding.tolist(),
        "augmentation": "mean",
        "created_at": datetime.utcnow().isoformat(),
    }
    supabase.table("student_embeddings").insert(row).execute()
    print("  ✔ Mean embedding saved.")


# ------------------------------------------------------------
#   MAIN REGISTRATION LOOP
# ------------------------------------------------------------
def main():
    print("\n=== Student Face Registration ===")
    print(f"  Roll No        : {UNIV_ROLL_NO}")
    print(f"  Captures       : {NUM_CAPTURES}")
    print(f"  Variants/frame : 30 augmentations")
    print(f"  Total vectors  : {NUM_CAPTURES * 30} → averaged to 1 mean embedding\n")

    student_uuid = get_student_uuid(UNIV_ROLL_NO)
    if student_uuid is None:
        return
    print(f"  Student UUID   : {student_uuid}\n")

    detector   = FaceDetector(Path(WEIGHTS_PATH), device=DEVICE, conf=CONF, iou=IOU, img_size=IMG_SIZE)
    recognizer = FaceRecognizer(device=DEVICE)

    src = MOBILE_CAM_URL if USE_MOBILE_CAMERA else 0
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print("[!] Could not open camera.")
        return
    print("  SPACE = capture  |  Q = quit\n")

    all_embeddings = []
    capture_count  = 0

    while capture_count < NUM_CAPTURES:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        remaining = NUM_CAPTURES - capture_count
        cv2.putText(frame, f"Capture {capture_count + 1}/{NUM_CAPTURES}  —  SPACE to capture",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Q to quit",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        cv2.imshow("Register Student", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            print("\n[!] Aborted by user.")
            break

        if key == ord(" "):
            print(f"\n[→] Capture {capture_count + 1}/{NUM_CAPTURES}")

            face_crop = extract_face_crop(frame, detector)
            if face_crop is None:
                print("  [!] No face found — this capture won't count, try again.")
                continue

            variants = augment_face(face_crop)
            print(f"  [→] {len(variants)} augmented variants generated")

            valid = 0
            for aug_img in variants:
                emb = recognizer.get_embedding(aug_img)
                if emb is not None:
                    all_embeddings.append(emb)
                    valid += 1

            capture_count += 1
            print(f"  [→] {valid}/{len(variants)} embeddings collected")
            print(f"  [→] Running total: {len(all_embeddings)} embeddings")

    cap.release()
    cv2.destroyAllWindows()

    if not all_embeddings:
        print("\n[!] No embeddings collected. Registration failed.")
        return

    # Compute + save mean
    print(f"\n[→] Computing mean embedding from {len(all_embeddings)} vectors...")
    mean_emb = compute_mean_embedding(all_embeddings)
    if mean_emb is None:
        print("[!] Failed to compute mean embedding.")
        return

    print("[→] Removing old embeddings...")
    delete_existing_embeddings(student_uuid)

    print("[→] Saving mean embedding to Supabase...")
    save_mean_embedding(student_uuid, mean_emb)

    print(f"\n✔ Registration complete!")
    print(f"  Captures used  : {capture_count}")
    print(f"  Vectors merged : {len(all_embeddings)}")
    print(f"  Stored         : 1 mean embedding\n")


if __name__ == "__main__":
    main()