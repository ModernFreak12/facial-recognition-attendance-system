import numpy as np
import cv2
import onnxruntime as ort
from app.config.config import FACE_RECOGNITION_MODEL, DEVICE


class FaceRecognizer:
    """
    ArcFace ONNX embedding extractor.
    This model expects:
        Input  : (1, 112, 112, 3)  NHWC
        Output : 512-dim embedding
    """

    def __init__(self,
                 model_path: str = str(FACE_RECOGNITION_MODEL),
                 device: str = DEVICE):

        providers = (
            ["CUDAExecutionProvider"] if device == "cuda"
            else ["CPUExecutionProvider"]
        )

        self.session = ort.InferenceSession(model_path, providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    # ---------------------------------------------------------
    # PREPROCESS → NHWC
    # ---------------------------------------------------------
    def preprocess(self, aligned_bgr: np.ndarray) -> np.ndarray:
        """
        Prepares aligned face for ArcFace ONNX (NHWC).
        """

        # BGR → RGB
        img = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB)

        # float32 normalization
        img = img.astype(np.float32)
        img = (img - 127.5) / 128.0

        # model expects NHWC, so keep shape (112,112,3)
        img = np.expand_dims(img, axis=0)  # (1,112,112,3)

        return img

    # ---------------------------------------------------------
    # EMBEDDING EXTRACTION
    # ---------------------------------------------------------
    def get_embedding(self, aligned_bgr: np.ndarray) -> np.ndarray:
        if aligned_bgr is None or aligned_bgr.size == 0:
            return None

        blob = self.preprocess(aligned_bgr)

        # ONNX forward pass
        out = self.session.run(None, {self.input_name: blob})[0]

        # flatten to (512,)
        out = out.reshape(-1).astype(np.float32)

        # L2 normalization
        norm = np.linalg.norm(out)
        if norm == 0:
            return None

        embedding = out / norm
        return embedding