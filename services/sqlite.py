import sqlite
import os
from config import settings

path_chunk = os.path.join(settings.faiss_index_path,"chunks.db")

chunk_db = os.makedirs(path_chunk,exist_ok=False)

CREATE_TABLE chunks


