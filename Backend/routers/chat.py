from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from services.claude_client import call_claude
from services.conversation_store import (
    append_message,
    clear_session,
    create_session,
    get_history,
    init_db,
    list_sessions,
)

router = APIRouter()
init_db()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    conversation_history: Optional[list[dict]] = None
    persist: bool = True


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    session_id: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or create_session()

        if request.conversation_history is not None:
            history = request.conversation_history
        elif request.persist:
            history = get_history(session_id)
        else:
            history = None

        reply = call_claude(
            user_message=request.message,
            system_prompt=request.system_prompt or "You are a helpful assistant.",
            conversation_history=history,
        )

        if request.persist:
            append_message(session_id, "user", request.message)
            append_message(session_id, "assistant", reply)

        return ChatResponse(
            reply=reply,
            model_used=settings.claude_model,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        return {"session_id": session_id, "messages": get_history(session_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History failed: {str(e)}")


@router.get("/sessions")
async def get_chat_sessions():
    try:
        return {"sessions": list_sessions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session listing failed: {str(e)}")


@router.delete("/history/{session_id}")
async def delete_chat_history(session_id: str):
    try:
        clear_session(session_id)
        return {"message": f"Deleted session {session_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/models")
async def get_model():
    return {"model": settings.claude_model}
