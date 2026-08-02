import time

from services.postgres.vector_store import query as vector_query
from services.postgres.vector_store import get_info
from services.claude_client import call_claude
from services.prompt import RAG_SYSTEM_PROMPT, HYDE_SYSTEM_PROMPT

_MIN_GAP     = 0.08
_FLOOR_SCORE = 0.10
_MIN_CHUNKS  = 2
_MAX_CHUNKS  = 8
def _get_n_candidates(user_id: int) -> int:
   index = get_info(user_id).get("total_vectors",0)
   if not index:
       return 0
   n_candidates = int(index * 0.2)
   return min(max(_MAX_CHUNKS+5,n_candidates),50)

def _generate_hypothetical_answer(question:str) -> str:
    return call_claude(user_message=question,system_prompt=HYDE_SYSTEM_PROMPT)


def _elapsed(start: float) -> float:
    return round(time.perf_counter() - start, 4)


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


def rag_query(
    user_question: str,
    user_id: int,
    system_prompt: str | None = None,
    use_hyde: bool = True,
) -> dict:
    total_start = time.perf_counter()
    metrics = {
        "retrieval_strategy": "hyde" if use_hyde else "raw_question",
        "use_hyde": use_hyde,
        "hyde_latency_seconds": 0.0,
        "candidate_count_latency_seconds": 0.0,
        "retrieval_latency_seconds": 0.0,
        "answer_generation_latency_seconds": 0.0,
        "total_latency_seconds": 0.0,
        "candidate_count": 0,
        "retrieved_candidate_count": 0,
        "chunks_used": 0,
    }

    if use_hyde:
        hyde_start = time.perf_counter()
        hypothetical_answer = _generate_hypothetical_answer(user_question)
        metrics["hyde_latency_seconds"] = _elapsed(hyde_start)
        retrieval_query = hypothetical_answer
    else:
        hypothetical_answer = ""
        retrieval_query = user_question

    count_start = time.perf_counter()
    candidate_count = _get_n_candidates(user_id)
    metrics["candidate_count_latency_seconds"] = _elapsed(count_start)
    metrics["candidate_count"] = candidate_count

    if candidate_count == 0:
        metrics["total_latency_seconds"] = _elapsed(total_start)
        return {
            "answer":           "No documents indexed yet. Please ingest documents first.",
            "retrieved_chunks": [],
            "sources":          [],
            "chunks_used":      0,
            "hyde_answer":      hypothetical_answer,
            "metrics":          metrics,
        }

    retrieval_start = time.perf_counter()
    candidates = vector_query(retrieval_query,candidate_count, user_id)
    metrics["retrieval_latency_seconds"] = _elapsed(retrieval_start)
    metrics["retrieved_candidate_count"] = len(candidates)

    retrieved = _dynamic_filtering(candidates)
    metrics["chunks_used"] = len(retrieved)
    if not retrieved:
        metrics["total_latency_seconds"] = _elapsed(total_start)
        return{
            "answer":  "No relevant information found. Try rephrasing your question.",
            "retrieved_chunks": [],
            "sources":          [],
            "chunks_used":      0,
            "hyde_answer":      hypothetical_answer,
            "metrics":          metrics,
        }
    
    context_block = "\n\n".join(f"[{i+1}] {chunk['text']}" for i, chunk in enumerate(retrieved))

    active_prompt = system_prompt or RAG_SYSTEM_PROMPT

    message = f"""Context: {context_block}
    ---
    Question: {user_question}

    """

    answer_start = time.perf_counter()
    answer = call_claude(message,active_prompt)
    metrics["answer_generation_latency_seconds"] = _elapsed(answer_start)
    metrics["total_latency_seconds"] = _elapsed(total_start)

    sources = list({
        chunk["metadata"].get("source", "unknown")
        for chunk in retrieved
    })

    return {
        "answer":           answer,
        "retrieved_chunks": retrieved,
        "sources":          sources,
        "chunks_used":      len(retrieved),
        "hyde_answer":      hypothetical_answer,
        "metrics":          metrics,
    }


    





   
   
