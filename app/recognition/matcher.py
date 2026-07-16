import numpy as np
import json
from numpy.linalg import norm
from collections import defaultdict
from app.services.supabase_client import supabase
from app.database.course_queries import get_students_for_course

THRESHOLD = 0.30 


def _parse_embedding(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("❌ ERROR: Cannot decode embedding string:", raw)
            return None
    print("❌ ERROR: Unsupported embedding format:", type(raw))
    return None


def load_embeddings(course_id=None):
    """
    Loads embeddings.

    If course_id is given:
        loads only enrolled students.

    Otherwise:
        loads all embeddings.
    """

    student_ids = []
    embeddings = []

    # -----------------------------
    # COURSE FILTERED MODE
    # -----------------------------
    if course_id:
        students = get_students_for_course(course_id)

        for student in students:
            emb = _parse_embedding(student["embedding"])

            if emb is None:
                continue

            if len(emb) != 512:
                print("❌ Wrong embedding size")
                continue

            student_ids.append(student["student_id"])
            embeddings.append(emb)

    # -----------------------------
    # LOAD EVERYTHING (fallback)
    # -----------------------------
    else:
        res = (
            supabase.table("student_embeddings")
            .select("student_id, embedding")
            .execute()
        )

        data = res.data or []

        for row in data:
            emb = _parse_embedding(row["embedding"])

            if emb is None:
                continue

            if len(emb) != 512:
                continue

            student_ids.append(row["student_id"])
            embeddings.append(emb)

    if not embeddings:
        return [], np.empty((0, 512), dtype=np.float32)

    embeddings = np.array(embeddings, dtype=np.float32)
    embeddings = embeddings / norm(embeddings, axis=1, keepdims=True)

    return student_ids, embeddings


class Matcher:
    """
    Matches ArcFace embeddings using cosine similarity.

    Strategy:
        - Each student has multiple embeddings (original + augmented variants)
        - For a query embedding, compute similarity against ALL stored embeddings
        - Group scores by student_id → take MAX score per student
        - Pick the student with the highest max score
        - Accept only if above THRESHOLD
    """

    def __init__(self, course_id=None):
        self.course_id = course_id
        self.student_ids, self.embeddings = load_embeddings(course_id)

    def reload(self):
        self.student_ids, self.embeddings = load_embeddings(self.course_id)

    def match(self, emb: np.ndarray):
        """
        Returns (student_id, score) or (None, score).
        """
        if emb is None or emb.shape[0] != 512:
            return None, 0.0

        emb = emb.astype(np.float32)
        emb_norm = norm(emb)
        if emb_norm == 0:
            return None, 0.0

        emb = emb / emb_norm

        if self.embeddings.size == 0:
            return None, 0.0

        # Cosine similarity — shape (N,)
        sims = self.embeddings @ emb

        # Group by student_id → max score per student
        student_best = defaultdict(float)
        for sid, sim in zip(self.student_ids, sims):
            if sim > student_best[sid]:
                student_best[sid] = float(sim)

        # Debug — print per-student best scores
        print("\n[DEBUG] Per-student best scores:")
        for sid, best in sorted(student_best.items(), key=lambda x: -x[1]):
            print(f"         {sid} → {best:.4f}")
        print(f"         Threshold : {THRESHOLD}")

        # Pick best student
        best_student = max(student_best, key=student_best.get)
        best_score = student_best[best_student]

        if best_score >= THRESHOLD:
            return best_student, best_score

        return None, best_score