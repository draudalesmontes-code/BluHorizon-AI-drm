import numpy as np
import os
import faiss
from config import settings

EMBEDDING_DIM = 384

_INDEX_FILE = os.path.join(settings.faiss_index_path,"faiss.index")

def _load_create() -> faiss.IndexFlatL2:
    os.makedirs(settings.faiss_index_path,exist_ok=True)
    if os.path.exists(_INDEX_FILE):
        return faiss.read_index(_INDEX_FILE)
    
    return faiss.IndexFlatIP(EMBEDDING_DIM)

FLAT = 