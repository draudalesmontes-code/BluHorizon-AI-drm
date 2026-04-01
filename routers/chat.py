from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.claude_client import call_claude

router = APIRouter()

class ChatRequest(message:str, system_prompt:str| None = None, onversation_history: list[dict] | None = None):


class ChatResponse():

async def chat(request: ChatRequest) -> ChatResponse:



async def get_model()-> dict:
