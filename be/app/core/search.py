#core/search.py
import numpy as np
from typing import List, Dict, Any
from typing import Tuple

def normalize_vectors(v: np.ndarray, axis: int = None) -> np.ndarray:
    norm = np.linalg.norm(v, axis=axis, keepdims=True) + 1e-8
    return v / norm

def best_similarity(embeddings: np.ndarray, query: np.ndarray) -> Tuple[int, float]:
    sims = embeddings.dot(query)
    idx = int(np.argmax(sims))
    return idx, float(sims[idx])

def search_similar_places(
    query_vector: List[float],
    place_data: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    q_vec = normalize_vectors(np.array(query_vector, dtype=np.float32))
    results = []
    for place in place_data:
        emb = np.array(place["embedding"], dtype=np.float32)
        emb_norm = normalize_vectors(emb, axis=1)
        top_idx, top_sim = best_similarity(emb_norm, q_vec)
        results.append({ "place_id": place["id"], "top_index": top_idx, "similarity": top_sim })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)[:top_k]
