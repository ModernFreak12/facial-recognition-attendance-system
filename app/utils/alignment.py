import cv2
import numpy as np


# ArcFace canonical 5-point reference template for 112×112 images
ARC_TEMPLATE = np.array([
    [38.2946, 51.6963],   # left eye
    [73.5318, 51.5014],   # right eye
    [56.0252, 71.7366],   # nose
    [41.5493, 92.3655],   # left mouth
    [70.7299, 92.2041],   # right mouth
], dtype=np.float32)


def align_face(face_bgr: np.ndarray, landmarks: np.ndarray,
               output_size: tuple = (112, 112)) -> np.ndarray:
    """
    Aligns a cropped BGR face to the ArcFace template.
    """

    if landmarks is None or len(landmarks) != 5:
        return None

    # Copy template and scale to output size
    dst = ARC_TEMPLATE.copy()
    if output_size != (112, 112):
        dst[:, 0] *= output_size[0] / 112
        dst[:, 1] *= output_size[1] / 112

    src = landmarks.astype(np.float32)

    # Find affine transform
    M = cv2.estimateAffinePartial2D(src, dst, method=cv2.LMEDS)[0]
    if M is None:
        return None

    # Warp with correct interpolation
    aligned = cv2.warpAffine(
        face_bgr,
        M,
        output_size,
        flags=cv2.INTER_LINEAR,
        borderValue=0
    )

    return aligned