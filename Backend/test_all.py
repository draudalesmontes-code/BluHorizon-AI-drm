"""
test_all.py — Quick manual test for all routers and tools
Run: python test_all.py
Server must be running: uvicorn main:app --reload
"""

import httpx
import asyncio

BASE = "http://localhost:8000"


def separator(title):
    print(f"\n{'='*40}")
    print(f" {title}")
    print('='*40)


# ── Routers ────────────────────────────────────────────────────────────────

def test_health():
    separator("Health Check")
    r = httpx.get(f"{BASE}/")
    print(r.json())


def test_chat():
    separator("Chat — basic message")
    r = httpx.post(f"{BASE}/chat/", json={
        "message": "What is RAG in one sentence?",
        "system_prompt": "You are a concise assistant."
    })
    print(r.json())


def test_chat_history():
    separator("Chat — multi turn")
    r = httpx.post(f"{BASE}/chat/", json={
        "message": "What is my name?",
        "conversation_history": [
            {"role": "user",      "content": "My name is Diego."},
            {"role": "assistant", "content": "Nice to meet you Diego!"}
        ]
    })
    print(r.json()["reply"])


def test_rag_ingest():
    separator("RAG — ingest document")
    r = httpx.post(f"{BASE}/rag/ingest", json={
        "text": "Dogs are mammals. They eat meat and dry kibble. Dogs live 10 to 15 years.",
        "source": "animals.txt",
        "doc_id": "doc1"
    }, timeout=30)
    print(r.json())


def test_rag_query():
    separator("RAG — query")
    r = httpx.post(f"{BASE}/rag/query", json={
        "question": "what do dogs eat?"
    }, timeout=60)
    data = r.json()
    print("answer:", data["answer"])
    print("chunks used:", data["chunks_used"])
    print("sources:", data["sources"])


def test_rag_stats():
    separator("RAG — stats")
    r = httpx.get(f"{BASE}/rag/stats")
    print(r.json())


def test_agent_search():
    separator("Agent — web search")
    r = httpx.post(f"{BASE}/agent/run", json={
        "message": "Search the web for what RAG means in AI"
    }, timeout=60)
    data = r.json()
    print("answer:", data["final_answer"][:200])
    print("tools called:", [t["tool_name"] for t in data["tool_calls_made"]])


def test_agent_code():
    separator("Agent — code execution")
    r = httpx.post(f"{BASE}/agent/run", json={
        "message": "Calculate compound interest on $10,000 at 5% for 10 years"
    }, timeout=60)
    data = r.json()
    print("answer:", data["final_answer"][:200])
    print("tools called:", [t["tool_name"] for t in data["tool_calls_made"]])


def test_agent_tools():
    separator("Agent — list tools")
    r = httpx.get(f"{BASE}/agent/tools")
    print(r.json())


# ── Tools (direct, no server needed) ──────────────────────────────────────

async def test_search_tool():
    separator("Tool — search direct")
    from tools.search_tool import run_search
    result = await run_search("what is retrieval augmented generation")
    print(result[:200])


def test_code_tool():
    separator("Tool — code direct")
    from tools.code_tool import run_code
    result = run_code("print(10000 * (1 + 0.05) ** 10)")
    print(result)


# ── Runner ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # tools — no server needed
    asyncio.run(test_search_tool())
    test_code_tool()

    # routers — server must be running
    test_health()
    test_chat()
    test_chat_history()
    test_rag_ingest()
    test_rag_query()
    test_rag_stats()
    test_agent_search()
    test_agent_code()
    test_agent_tools()

    print("\n✓ All tests complete")