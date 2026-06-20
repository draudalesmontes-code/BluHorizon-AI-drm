"""Throwaway diagnostic: test pgvector retrieval directly for a user."""
from services.postgres.vector_store import query, get_info
from services.rag_pipeline import rag_query

USER_ID = 1
SAMPLE_QUERY = "work experience, skills, and education"

print("=== get_info ===")
print(get_info(USER_ID))

print("\n=== raw vector_store.query (no HyDE, no floor filter) ===")
results = query(SAMPLE_QUERY, 10, USER_ID)
print(f"returned {len(results)} chunks")
for r in results:
    print(f"  score={r['score']:.3f}  source={r['metadata']['source']}  text={r['text'][:70]!r}")

print("\n=== full rag_query (HyDE + filtering) ===")
out = rag_query("Summarize the resume", USER_ID)
print("chunks_used:", out["chunks_used"])
print("sources:", out["sources"])
print("answer:", out["answer"][:300])
