from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.chat import router as chat
from routers.rag import router as rag
from routers.agents import router as agents

app = FastAPI(title="Agentic AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health() -> dict:
    return {"status": "ok"}

app.include_router(chat, prefix="/chat", tags=["chat"])
app.include_router(rag, prefix="/rag", tags=["rag"])
app.include_router(agents, prefix="/agents", tags=["agents"])