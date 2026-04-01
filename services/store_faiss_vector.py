import os
import faiss
import numpy as np
from config import settings

from services.embedding import chunk_text, embed_batch, embed_text
from services.index_faiss_vector import add_vectors, search
from services import sqlite

def add_document(text: str, metadata: dict =None) -> list[int]:
    metadata = metadata or {}
    
    chunks_of_text = chunk_text(text)
    embedded_results = embed_batch(chunks_of_text)
    list_of_vectors_ids = add_vectors(embedded_results)
    sqlite.insert_chunks([{
        "id":chunk_id,
        "text":chunk,
        "source":metadata.get("source"),
        "doc_id":metadata.get("doc_id")
    }
    for chunk_id, chunk in zip(list_of_vectors_ids, chunks_of_text)
    ])

    return list_of_vectors_ids


def query(query_text:str, n_results:int) -> list[dict]:
    text_vector = embed_text(query_text)
    matches = search(text_vector,n_results)
    rows = sqlite.fetch_by_ids([m[0] for m in matches])

    results = []
    for chunk_id, score in matches:   
        row = rows.get(chunk_id)

        if not row:
            continue

        results.append({
            "text":     row["text"],
            "id":       chunk_id,
            "metadata": {
                "source": row["source"],
                "doc_id": row["doc_id"]
            },
            "score": score
        })

    return results

def get_info() ->dict:
    from services.index_faiss_vector import get_stats as faiss_stats
    from services.sqlite import get_stats as db_stats
    return {**faiss_stats(),**db_stats()}




    
