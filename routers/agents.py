from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.claude_client import call_claude_tools
from services.prompt import AGENT_SYSTEM_PROMPT
from tools.code_tool import CODE_TOOL_DEFINITION, run_code
from tools.search_tool import SEARCH_TOOL_DEFINITION, run_search

router = APIRouter()


class AgentRequest(BaseModel):
    message: str
    conversation_history: list[dict] | None = None


class AgentResponse(BaseModel):
    reply: str


@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        tools = [CODE_TOOL_DEFINITION, SEARCH_TOOL_DEFINITION]

        response = call_claude_tools(
            user_message=request.message,
            tools=tools,
            system_prompt=AGENT_SYSTEM_PROMPT,
            conversation_history=request.conversation_history
        )

        if response.stop_reason == "end_turn":
            return AgentResponse(reply=response.content[0].text)

        if response.stop_reason == "tool_use":
            tool_block = next(
                block for block in response.content
                if block.type == "tool_use"
            )

            if tool_block.name == "execute_python":
                tool_result = run_code(tool_block.input["code"])
                return AgentResponse(
                    reply=f"Tool used: execute_python\n\nResult:\n{tool_result}"
                )

            if tool_block.name == "web_search":
                tool_result = await run_search(tool_block.input["query"])
                return AgentResponse(
                    reply=f"Tool used: web_search\n\nResult:\n{tool_result}"
                )

            raise HTTPException(
                status_code=400,
                detail=f"Unknown tool requested: {tool_block.name}"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected stop reason: {response.stop_reason}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")