from pathlib import Path
from typing import Optional
import numpy as np
import cv2
import onnxruntime as ort

from app.config.config import LANDMARK_MODEL


class LandmarkDetector:
    """
    68-landmark 2DFAN4 model.
    We convert the 68 points into 5 points for ArcFace alignment.
    """

    def __init__(self, model_path: Path = LANDMARK_MODEL, device: str = "cpu"):
        providers = (
            ["CUDAExecutionProvider"] if device == "cuda"
            else ["CPUExecutionProvider"]
        )

        self.session = ort.InferenceSession(str(model_path), providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, face_crop_bgr: np.ndarray) -> Optional[np.ndarray]:
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return None

        # Resize to 256×256
        img = cv2.resize(face_crop_bgr, (256, 256))

        # BGR → RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = img.astype(np.float32) / 255.0

        # NHWC → NCHW
        img = np.transpose(img, (2, 0, 1))[None, :]

        # Inference
        out = self.session.run(None, {self.input_name: img})[0].flatten()

        # Model outputs 68 × 3 = 204 values → reshape
        pts = out.reshape(-1, 3)[:, :2]  # take (x, y), ignore score
        pts = pts.reshape(68, 2)

        # Rescale to original face crop size
        h, w = face_crop_bgr.shape[:2]
        pts[:, 0] *= w
        pts[:, 1] *= h

        # ------------------------------
        # CONVERT 68 → 5 LANDMARKS
        # ------------------------------

        # Eyes center = average of 6 eye points each
        left_eye = pts[36:42].mean(axis=0)
        right_eye = pts[42:48].mean(axis=0)

        nose = pts[30]
        left_mouth = pts[48]
        right_mouth = pts[54]

        landmarks_5 = np.vstack([
            left_eye,
            right_eye,
            nose,
            left_mouth,
            right_mouth
        ])

        return landmarks_5