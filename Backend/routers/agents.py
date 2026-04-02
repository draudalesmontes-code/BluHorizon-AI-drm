from typing import Optional

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.claude_client import call_claude_tools
from services.conversation_store import (
    append_message,
    create_session,
    get_history,
    init_db,
)
from services.prompt import AGENT_SYSTEM_PROMPT

router = APIRouter()
init_db()


def get_all_tools() -> dict[str, dict]:
    from tools.code_tool import CODE_TOOL_DEFINITION
    from tools.rag_tool import RAG_TOOL_DEFINITION
    from tools.search_tool import SEARCH_TOOL_DEFINITION

    return {
        "web_search": SEARCH_TOOL_DEFINITION,
        "execute_python": CODE_TOOL_DEFINITION,
        "search_documents": RAG_TOOL_DEFINITION,
    }


class AgentRequest(BaseModel):
    message: str = Field(..., description="User message.")
    session_id: Optional[str] = Field(None, description="Persistent conversation/session id.")
    persist: bool = Field(True, description="Whether to save and reuse conversation history.")
    conversation_history: Optional[list[dict]] = Field(None, description="Optional direct history override.")
    use_web_search: bool = Field(True, description="Enable web search tool.")
    use_code: bool = Field(False, description="Enable code execution tool.")
    use_rag: bool = Field(True, description="Enable RAG document search.")
    max_tool_calls: int = Field(5, description="Max tool calls before stopping.")
    system_prompt: Optional[str] = Field(None, description="Optional custom system prompt.")


class ToolCallLog(BaseModel):
    tool_name: str
    tool_input: dict
    tool_output: str


class AgentResponse(BaseModel):
    final_answer: str
    tool_calls_made: list[ToolCallLog]
    total_turns: int
    session_id: str


async def run_agent_loop(
    user_message: str,
    tools: list[dict],
    system_prompt: str,
    max_tool_calls: int,
    seed_history: Optional[list[dict]] = None,
) -> tuple[str, list[ToolCallLog], int]:
    if not tools:
        from services.claude_client import call_claude

        answer = call_claude(
            user_message=user_message,
            system_prompt=system_prompt,
            conversation_history=seed_history,
        )
        return answer, [], 1

    conversation: list[dict] = list(seed_history or [])
    conversation.append({"role": "user", "content": user_message})

    tool_logs: list[ToolCallLog] = []
    turns = 0

    while turns < max_tool_calls:
        turns += 1

        response = call_claude_tools(
            user_message="",
            tools=tools,
            system_prompt=system_prompt,
            conversation_history=conversation,
        )

        conversation.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = " ".join(
                block.text
                for block in response.content
                if isinstance(block, anthropic.types.TextBlock)
            )
            return final_text, tool_logs, turns

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if not isinstance(block, anthropic.types.ToolUseBlock):
                    continue

                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                if tool_name == "web_search":
                    from tools.search_tool import run_search
                    tool_output = await run_search(tool_input["query"])
                elif tool_name == "execute_python":
                    from tools.code_tool import run_code
                    tool_output = run_code(tool_input["code"])
                elif tool_name == "search_documents":
                    from tools.rag_tool import run_rag
                    tool_output = await run_rag(tool_input["query"])
                else:
                    tool_output = f"Unknown tool: {tool_name}"

                tool_logs.append(
                    ToolCallLog(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_output=tool_output,
                    )
                )

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_output,
                    }
                )

            conversation.append({"role": "user", "content": tool_results})

    return "Maximum tool calls reached. Try a simpler request.", tool_logs, turns


@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        all_tools = get_all_tools()

        tools = []
        if request.use_web_search:
            tools.append(all_tools["web_search"])
        if request.use_code:
            tools.append(all_tools["execute_python"])
        if request.use_rag:
            tools.append(all_tools["search_documents"])

        active_prompt = request.system_prompt or AGENT_SYSTEM_PROMPT
        session_id = request.session_id or create_session()

        if request.conversation_history is not None:
            seed_history = request.conversation_history
        elif request.persist:
            seed_history = get_history(session_id)
        else:
            seed_history = []

        final_answer, tool_logs, turns = await run_agent_loop(
            user_message=request.message,
            tools=tools,
            system_prompt=active_prompt,
            max_tool_calls=request.max_tool_calls,
            seed_history=seed_history,
        )

        if request.persist:
            append_message(session_id, "user", request.message)
            append_message(session_id, "assistant", final_answer)

        return AgentResponse(
            final_answer=final_answer,
            tool_calls_made=tool_logs,
            total_turns=turns,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


@router.get("/tools")
async def list_tools():
    all_tools = get_all_tools()
    return {
        "available_tools": [
            {
                "name": name,
                "description": defn["description"],
                "parameters": list(defn["input_schema"]["properties"].keys()),
            }
            for name, defn in all_tools.items()
        ]
    }
