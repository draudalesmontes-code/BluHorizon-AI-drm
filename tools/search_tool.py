from tavily import TavilyClient
from config import settings

_tavily = TavilyClient(api_key=settings.tavily_api_key)


SEARCH_TOOL_DEFINITION = { 
    {
        "name": "web_search",
        "description": (
        "Search the web for current information. Use this when the user asks "
        "about recent events, real-time data, or facts that may not be in "
        "your training data. Returns a text summary of search results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
            "query": {
                  "type": "string",
                "description": "The search query to look up on the web."
            }
            },
            "required": ["query"]
        }
    }
}

async def run_search(query: str) ->str:
    result = _tavily.search(query=query,max_results=5)

    contents = [
        r["content"]
        for r in result.get("results",[])
        if r.get("content")
    ]

    if not contents:
        return f"No results found for: {query}"
    
    return "\n\n---\n\n".join(contents)




