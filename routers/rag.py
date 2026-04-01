from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.claude_client import call_claude

router = APIRouter()
