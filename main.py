from fastapi import FastAPI
from pydantic import BaseModel
from anthropic import Anthropic
from config import settings

app = FastAPI()
client = Anthropic(api_key=settings.anthropic_api_key) 


@app.get("/")
def health():
    return {"status": "ok"}



@app.post("/chat")
def chat(message: str):
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=settings.max_tokens,
        messages=[{
            "role":"user",
            "content":message
        }]
    )
    return {"reply": response.content[0].text}



