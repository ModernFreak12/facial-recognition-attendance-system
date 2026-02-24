import numpy as np
import json
from numpy.linalg import norm
from app.services.supabase_client import supabase


THRESHOLD = 0.55  # ArcFace recommended threshold ~0.5–0.6


def _parse_embedding(raw):
    """
    Converts raw Supabase embedding into a Python float list.

    Supabase may return:
        - list[float]
        - or string: "[-0.02, 0.11, ...]"
    """

    # Case 1: Already a list of floats
    if isinstance(raw, list):
        return raw

    # Case 2: String representing a list
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("❌ ERROR: Cannot decode embedding string:", raw)
            return None

    # Unsupported type
    print("❌ ERROR: Unsupported embedding format:", type(raw))
    return None


def load_embeddings():
    """
    Loads student embeddings from Supabase.
    Ensures all embeddings are float32 and L2-normalized.

    Returns:
        student_ids : list[str]
        embeddings  : np.ndarray (N, 512)
    """
    res = (
        supabase
        .table("student_embeddings")
        .select("student_id, embedding")
        .execute()
    )

    data = res.data or []

    student_ids = []
    embeddings = []

    for row in data:
        emb = _parse_embedding(row["embedding"])
        if emb is None:
            continue

        # Ensure correct length
        if len(emb) != 512:
            print(f"❌ Skipping embedding with wrong dimension: {len(emb)}")
            continue

        student_ids.append(row["student_id"])
        embeddings.append(emb)

    if not embeddings:
        return [], np.empty((0, 512), dtype=np.float32)

    embeddings = np.array(embeddings, dtype=np.float32)

    # Normalize
    embeddings = embeddings / norm(embeddings, axis=1, keepdims=True)

    return student_ids, embeddings


class Matcher:
    """
    Matches ArcFace embeddings using cosine similarity.
    """

    def __init__(self):
        self.student_ids, self.embeddings = load_embeddings()

    def reload(self):
        """Reload DB embeddings."""
        self.student_ids, self.embeddings = load_embeddings()

    def match(self, emb: np.ndarray):
        """
        Given a 512-dim L2-normalized embedding,
        returns (student_id, score) or (None, score).
        """

        if emb is None or emb.shape[0] != 512:
            return None, 0.0

        # Normalize input embedding
        emb = emb.astype(np.float32)
        emb_norm = norm(emb)

        if emb_norm == 0:
            return None, 0.0

        emb = emb / emb_norm

        if self.embeddings.size == 0:
            return None, 0.0

        # Cosine similarity via dot product
        sims = self.embeddings @ emb

        idx = int(np.argmax(sims))
        score = float(sims[idx])

        if score >= THRESHOLD:
            return self.student_ids[idx], score

        return None, score