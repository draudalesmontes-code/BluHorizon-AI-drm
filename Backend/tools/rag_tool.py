RAG_TOOL_DEFINITION = {
    "name": "search_documents",
    "description": (
        "Search the indexed knowledge base for relevant information. "
        "Use this when the user asks about topics that may exist in "
        "the uploaded documents. Returns relevant text passages with citations."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant documents."
            }
        },
        "required": ["query"]
    }
}


async def run_rag(query: str) -> str:

    from services.rag_pipeline import rag_query
    result = rag_query(query)

    if not result.get("retrieved_chunks"):
        return "No relevant documents found for this query."

    sources = ", ".join(result.get("sources", []))
    answer  = result.get("answer", "No answer generated.")

    return f"{answer}\n\nSources: {sources}" if sources else answer