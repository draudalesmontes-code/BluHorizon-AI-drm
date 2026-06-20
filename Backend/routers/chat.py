from typing import Optional

from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel

from dependencies import get_current_user
from config import settings
from services.claude_client import call_claude
from services.postgres.postgres_store import (
    append_message,
    clear_conversation,
    create_conversation,
    get_history,
    list_conversations,
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    system_prompt: Optional[str] = None
    conversation_history: Optional[list[dict]] = None
    persist: bool = True


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    conversation_id: int


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, user_id: int = Depends(get_current_user)):
    try:
        conversation_id = request.conversation_id or create_conversation(user_id)

        if request.conversation_history is not None:
            history = request.conversation_history
        elif request.persist:
            history = get_history(conversation_id, user_id)
        else:
            history = None

        reply = call_claude(
            user_message=request.message,
            system_prompt=request.system_prompt or "You are a helpful assistant.",
            conversation_history=history,
        )

        if request.persist:
            append_message(conversation_id, "user", request.message)
            append_message(conversation_id, "assistant", reply)

        return ChatResponse(
            reply=reply,
            model_used=settings.claude_model,
            conversation_id=conversation_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history/{conversation_id}")
async def get_chat_history(conversation_id: int ,user_id: int = Depends(get_current_user)):
    try:
        return {"conversation_id": conversation_id, "messages": get_history(conversation_id, user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History failed: {str(e)}")


@router.get("/sessions")
async def get_chat_sessions(user_id: int = Depends(get_current_user)):
    try:
        return {"conversations": list_conversations(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"conversation listing failed: {str(e)}")


@router.delete("/history/{conversation_id}")
async def delete_chat_history(conversation_id: int, user_id: int = Depends(get_current_user)):
    try:
        clear_conversation(conversation_id, user_id)
        return {"message": f"Deleted conversation {conversation_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/models")
async def get_model(user_id: int = Depends(get_current_user)):
    return {"model": settings.claude_model}
