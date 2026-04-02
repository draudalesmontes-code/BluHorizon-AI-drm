from services.store_faiss_vector import query as vector_query
from services.store_faiss_vector import get_info
from services.claude_client import call_claude
from services.prompt import RAG_SYSTEM_PROMPT, HYDE_SYSTEM_PROMPT

_MIN_GAP     = 0.12
_FLOOR_SCORE = 0.50
_MIN_CHUNKS  = 2
_MAX_CHUNKS  = 8
def _get_n_candidates() -> int:
   index = get_info().get("total_vectors",0)
   if not index:
       return 0
   n_candidates = int(index * 0.2)
   return min(max(_MAX_CHUNKS+5,n_candidates),50)

def _generate_hypothetical_answer(question:str) -> str:
    return call_claude(user_message=question,system_prompt=HYDE_SYSTEM_PROMPT)


def _dynamic_filtering(candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    above_floor = [c for c in candidates if c["score"] >= _FLOOR_SCORE]
    if not above_floor:
        return []
    if len(above_floor) <= _MIN_CHUNKS:
        return above_floor
    gaps = [above_floor[i]["score"]-above_floor[i+1]["score"] for i in range(len(above_floor)-1)]
    biggest_gap = max(gaps) 
    biggest_drop_index = gaps.index(biggest_gap)
    if biggest_gap >= _MIN_GAP:
        cut_at = biggest_drop_index + 1
    else:
        cut_at = len(above_floor)

    cut_at = max(cut_at,_MIN_CHUNKS)
    cut_at = min(cut_at,_MAX_CHUNKS)

    return above_floor[:cut_at]

def rag_query(user_question:str, system_prompt:str| None = None)-> dict:
    hypothetical_answer = _generate_hypothetical_answer(user_question)
    candidate_count = _get_n_candidates()
    if candidate_count == 0:
        return {
            "answer":           "No documents indexed yet. Please ingest documents first.",
            "retrieved_chunks": [],
            "sources":          [],
            "chunks_used":      0,
            "hyde_answer":      hypothetical_answer
        }
    candidates = vector_query(hypothetical_answer,candidate_count)
    retrieved = _dynamic_filtering(candidates)
    if not retrieved:
        return{
            "answer":  "No relevant information found. Try rephrasing your question.",
            "retrieved_chunks": [],
            "sources":          [],
            "chunks_used":      0,
            "hyde_answer":      hypothetical_answer
        }
    
    context_block = "\n\n".join(f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(retrieved))

    active_prompt = system_prompt or RAG_SYSTEM_PROMPT

    message = f"""Context: {context_block}
    ---
    Question: {user_question}

    """

    answer = call_claude(message,active_prompt)

    sources = list({
        chunk["metadata"].get("source", "unknown")
        for chunk in retrieved
    })

    return {
        "answer":           answer,
        "retrieved_chunks": retrieved,
        "sources":          sources,
        "chunks_used":      len(retrieved),
        "hyde_answer":      hypothetical_answer
    }


    





   
   

