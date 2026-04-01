import numpy as np
import os
import faiss
from config import settings

EMBEDDING_DIM = 384

_INDEX_FILE = os.path.join(settings.faiss_index_path,"faiss.index")

def _load_create() -> faiss.IndexFlatIP:
    os.makedirs(settings.faiss_index_path,exist_ok=True)
    if os.path.exists(_INDEX_FILE):
        return faiss.read_index(_INDEX_FILE)
    
    return faiss.IndexFlatIP(EMBEDDING_DIM)


def _save() -> None:
    faiss.write_index(_index,_INDEX_FILE)
    

_index = _load_create()



def add_vectors(vectors: np.ndarray)-> list[int]:
    vectors = np.array(vectors,dtype=np.float32)
    faiss.normalize_L2(vectors)
    start_id = _index.ntotal
    _index.add(vectors) 
    _save()
    return list(range(start_id,_index.ntotal))


def search(query_vector: list[float], k: int = 5) -> list[tuple[int, float]]:
    if _index.ntotal == 0:
        return []
    
    query = np.array([query_vector],np.float32)

    faiss.normalize_L2(query)

    k = min(k, _index.ntotal)
    distances, indices = _index.search(query, k)
       

    return [
        (int(idx), round(float(score), 4))
        for score, idx in zip(distances[0], indices[0])
        if idx != -1
    ]

    
def get_stats() -> dict:
    return {
        "total_vectors": _index.ntotal,
        "embedding_dim": EMBEDDING_DIM,
        "index_type":    type(_index).__name__
    }