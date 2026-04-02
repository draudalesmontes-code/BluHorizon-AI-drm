from services.claude_client import call_claude
# used in rag_pipeline.py for the final answer generation
RAG_SYSTEM_PROMPT = """You are a helpful assistant. Answer questions using ONLY
the context provided below. If the context does not contain the answer say so
clearly. Cite which snippet you used, for example: According to [1]..."""

# used in rag_pipeline.py for HyDE hypothetical answer generation
HYDE_SYSTEM_PROMPT = (
    "Generate a detailed hypothetical answer to the question below. "
    "Write it as if you are certain even if you are not. "
    "This is used for document retrieval only — not shown to the user. "
    "Be specific and use technical language relevant to the topic."
)

# used in routers/agent.py for the agent loop
AGENT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant with access to tools. "
    "Use tools when you need current information or need to perform calculations. "
    "Always explain what you are doing and why."
)

# used internally by generate_system_prompt()
# tells Claude it is acting as a prompt engineer
_PROMPT_GENERATOR_PROMPT = """You are an expert prompt engineer.
Your job is to write clear, focused system prompts for AI assistants.
When given a description of a use case, return ONLY the system prompt text.
No explanation, no preamble, no quotes around it — just the prompt itself.
The prompt should be specific, concise, and guide the AI toward the desired behavior."""



def generate_system_prompt(use_case: str) -> str:
    """
    Ask Claude to generate a focused system prompt for a specific use case.

    WHY THIS EXISTS:
        generic RAG prompt works for general questions
        but specific domains need narrowed prompts
        example: medical docs need different tone than legal docs
        instead of writing prompts manually let Claude generate them
        caller can store the result and reuse it

    Args:
        use_case: plain description of what you want the prompt to do
                  example: "a RAG assistant that only answers questions
                            about Python programming using formal language"

    Returns:
        a system prompt string ready to pass to call_claude()

    Example:
        prompt = generate_system_prompt(
            "a RAG assistant for medical documents that always
             recommends consulting a doctor and uses simple language"
        )
        result = rag_query(question, system_prompt=prompt)
    """
    return call_claude(
        user_message=use_case,
        system_prompt=_PROMPT_GENERATOR_PROMPT
    )