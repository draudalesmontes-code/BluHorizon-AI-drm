import anthropic
from config import settings

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# WHY TWO FUNCTIONS:
# Claude returns two completely different response shapes:
#
#   no tools → stop_reason="end_turn"  → response always has text
#              → safe to extract .text immediately
#
#   tools    → stop_reason="end_turn"  → response has text
#            → stop_reason="tool_use"  → response has tool call, NO text
#              → extracting .text on a tool_use response crashes
#
# call_claude()            → no tools → always returns plain string
# call_claude_with_tools() → has tools → returns full object so caller
#                            can check stop_reason before touching .text




def call_claude(user_message: str, system_prompt: str ="You are a helpfull assistant", conversation_history: list[dict] | None = None) -> str:
    messages_list =  (conversation_history or []) + [{
        "role":"user",
        "content": user_message}]
    
    response = _client.messages.create(
        model= settings.claude_model,
        max_tokens=settings.max_tokens,
        system= system_prompt,
        messages = messages_list
    )

    return response.content[0].text

def call_claude_tools(user_message:str, tools: list[dict], system_prompt:str, conversation_history: list[dict] | None = None)-> anthropic.types.Message:
    message = (conversation_history or []) + [{
        "role":"user",
        "content": user_message
    }]

    return  _client.messages.create(
        model=settings.claude_model,
        max_tokens=settings.max_tokens,
        system=system_prompt,
        tools=tools,
        messages=message
    )


