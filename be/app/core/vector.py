#core/vector.py
import numpy as np
from typing import Tuple

def normalize_vectors(v: np.ndarray, axis: int = None) -> np.ndarray:
    norm = np.linalg.norm(v, axis=axis, keepdims=True) + 1e-8
    return v / norm

def best_similarity(embeddings: np.ndarray, query: np.ndarray) -> Tuple[int, float]:
    sims = embeddings.dot(query)
    idx = int(np.argmax(sims))
    return idx, float(sims[idx])
