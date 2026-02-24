import cv2
import numpy as np

ARC_TEMPLATE = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
], dtype=np.float32)


def align_face(face_bgr: np.ndarray, landmarks: np.ndarray,
               output_size: tuple = (112, 112)) -> np.ndarray | None:
    """
    face_bgr  : the 112x112 resized crop (must match the space landmarks are in)
    landmarks : (5, 2) from LandmarkDetector.predict()
    """
    if landmarks is None or landmarks.shape != (5, 2):
        return None

    dst = ARC_TEMPLATE.copy()
    if output_size != (112, 112):
        dst[:, 0] *= output_size[0] / 112
        dst[:, 1] *= output_size[1] / 112

    src = landmarks.astype(np.float32)
    M = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)[0]
    if M is None:
        return None

    aligned = cv2.warpAffine(
        face_bgr, M, output_size,
        flags=cv2.INTER_LINEAR,
        borderValue=0
    )
    return aligned