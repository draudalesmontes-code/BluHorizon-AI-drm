from fastapi import FastAPI
from pydantic import BaseModel
from anthropic import Anthropic
from config import settings

from routers.chat import router as chat
from routers.rag import router as rag
from routers.agents import router as agents

app = FastAPI(title="Agentic AI API")

@app.get("/")
def health() -> dict:
    return {"status": "ok"}


app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(rag_router, prefix="/rag", tags=["rag"])
app.include_router(agents_router, prefix="/agents", tags=["agents"])


