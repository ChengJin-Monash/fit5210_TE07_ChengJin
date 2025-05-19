import os
from typing import AsyncGenerator, List, Dict
from llama_cpp import Llama

from chatbot_config import LOCAL_MODEL_PATH, LOCAL_GEN_CONFIG

# -----------------------------------------------------------------------------
# Model Initialization
# -----------------------------------------------------------------------------
# Cache for the Llama model instance to avoid reloading on each call.
_llm: Llama = None

def init_model() -> Llama:
    """
    Initialize and cache the Llama model instance.

    Uses the LOCAL_MODEL_PATH and config parameters from LOCAL_GEN_CONFIG.
    Subsequent calls return the already loaded model to improve performance.
    """
    global _llm
    if _llm is None:
        # Instantiate the Llama model with context window and thread settings
        _llm = Llama(
            model_path=LOCAL_MODEL_PATH,
            n_ctx=LOCAL_GEN_CONFIG.get("n_ctx", 2048),
            n_threads=LOCAL_GEN_CONFIG.get("n_threads", 6)
        )
    return _llm

# -----------------------------------------------------------------------------
# Default System Prompt Loading
# -----------------------------------------------------------------------------
def get_default_system_prompt() -> str:
    """
    Read and return the system prompt text from file.

    The system prompt defines the assistant's persona and initial instructions.
    """
    path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

# -----------------------------------------------------------------------------
# Construct Chat Messages List
# -----------------------------------------------------------------------------
def build_messages(prompt: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Assemble the full list of chat messages for the model.

    The list consists of:
      1. A system message loaded from the system prompt file.
      2. All previous messages from history.
      3. The current user prompt.

    Args:
        prompt: The latest user input.
        history: List of prior messages, each a dict with 'role' and 'content'.

    Returns:
        A list of message dicts suitable for create_chat_completion().
    """
    # Start with the system message to establish context
    messages = [{"role": "system", "content": get_default_system_prompt()}]
    # Append the existing conversation history
    messages.extend(history)
    # Finally include the new user prompt
    messages.append({"role": "user", "content": prompt})
    return messages

# -----------------------------------------------------------------------------
# Streaming Chat Output via TinyLLaMA
# -----------------------------------------------------------------------------
async def tinyllama_stream(
    prompt: str,
    session_id: str,
    history: List[Dict[str, str]]
) -> AsyncGenerator[str, None]:
    """
    Stream chat responses from the local TinyLLaMA model.

    Uses Llama's create_chat_completion with stream=True to yield tokens
    incrementally as they are generated.

    Args:
        prompt: The user's latest input.
        session_id: Identifier for this conversation (unused here but kept for interface consistency).
        history: Full conversation history for context.

    Yields:
        Individual text fragments as the model produces them.
    """
    # Initialize or retrieve the cached model
    llm = init_model()
    # Build the message sequence including system, history, and user prompt
    messages = build_messages(prompt, history)

    # Begin streaming completion tokens
    streamer = llm.create_chat_completion(
        messages=messages,
        stream=True,
        max_tokens=LOCAL_GEN_CONFIG.get("MAX_TOKENS", LOCAL_GEN_CONFIG.get("max_tokens", 512)),
        temperature=LOCAL_GEN_CONFIG.get("TEMPERATURE", LOCAL_GEN_CONFIG.get("temperature", 0.7))
    )

    # Iterate over each chunk returned by the streamer
    for chunk in streamer:
        # Extract the content delta from the first choice
        data = chunk.get("choices", [])[0]
        delta = data.get("delta", {})
        content = delta.get("content")
        # Yield only if there is actual text content
        if content:
            yield content

# -----------------------------------------------------------------------------
# One-Shot Chat Output via TinyLLaMA
# -----------------------------------------------------------------------------
async def tinyllama_once(
    prompt: str,
    session_id: str,
    history: List[Dict[str, str]]
) -> str:
    """
    Perform a single-turn chat completion with the TinyLLaMA model.

    Uses Llama's create_chat_completion with stream=False to get the full
    response in one call.

    Args:
        prompt: The user's latest input.
        session_id: Identifier for this conversation (unused here but kept for interface consistency).
        history: Full conversation history for context.

    Returns:
        The complete text response from the model.
    """
    # Initialize or retrieve the cached model
    llm = init_model()
    # Build the message sequence including system, history, and user prompt
    messages = build_messages(prompt, history)

    # Request a non-streaming chat completion
    response = llm.create_chat_completion(
        messages=messages,
        stream=False,
        max_tokens=LOCAL_GEN_CONFIG.get("MAX_TOKENS", LOCAL_GEN_CONFIG.get("max_tokens", 512)),
        temperature=LOCAL_GEN_CONFIG.get("TEMPERATURE", LOCAL_GEN_CONFIG.get("temperature", 0.7))
    )

    # Extract and return the generated content from the first choice
    result = response.get("choices", [])[0]
    return result.get("message", {}).get("content", "")
