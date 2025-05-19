import os
import json
import logging
import httpx
from typing import AsyncGenerator, List, Dict, Tuple

from chatbot_config import API_KEY, BASE_URL, MODEL_NAME
from session_manager import load_history, save_history

# Create a module-specific logger for diagnostic and audit messages.
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# System Prompt Loading
# -----------------------------------------------------------------------------
# The system prompt establishes the assistant’s persona, instructions, and
# any initial context required by the language model on each invocation.
# It is read once at module import time to avoid repeated file I/O.
_dir = os.path.dirname(__file__)
_SYSTEM_PROMPT_PATH = os.path.join(_dir, "system_prompt.txt")

try:
    # Open the system prompt file in UTF-8 to support international characters.
    with open(_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
    if not SYSTEM_PROMPT:
        raise ValueError("system_prompt.txt is empty")
    logger.debug("System prompt loaded successfully")
except Exception as e:
    # Fail fast if the system prompt cannot be loaded, as it is critical to operation.
    logger.critical(f"Failed to load system prompt from {_SYSTEM_PROMPT_PATH}: {e}")
    raise


def _build_contents_and_instruction(
    history: List[Dict[str, str]]
) -> Tuple[List[Dict[str, List[Dict[str, str]]]], Dict]:
    """
    Build request payload components:
    - system_inst: the system-level instruction prompt
    - contents: the list of user and assistant messages from history
    """
    # Prepare the system instruction payload if a system prompt is defined
    system_inst: Dict = {"parts": [{"text": SYSTEM_PROMPT}]} if SYSTEM_PROMPT else {}

    # Initialize the contents list for user and assistant message payloads
    contents: List[Dict] = []

    # Iterate through each message in the conversation history
    for msg in history:
        # Determine the message role, defaulting to 'user' if not provided
        role = msg.get("role", "user")

        # Skip messages with the 'system' role
        if role == "system":
            continue

        # Extract and trim the message content
        text = msg.get("content", "").strip()

        # Include only non-empty messages in the payload
        if text:
            contents.append({
                "role": role,
                "parts": [{"text": text}]
            })

    # Return the formatted conversation contents and the system instruction
    return contents, system_inst


async def gemini_stream(
    prompt: str, session_id: str, history: List[Dict[str, str]]
) -> AsyncGenerator[str, None]:
    """
    Stream tokens from the Google Gemini API using the /streamGenerateContent endpoint.

    Args:
        prompt (str): The latest user prompt to send to the model.
        session_id (str): Unique identifier for the conversation session.
        history (List[Dict[str, str]]): Full conversation history including the new prompt.

    Yields:
        str: Individual text chunks as they arrive from the API stream.
    """
    # Build the message contents and optional system instruction from history
    contents, system_inst = _build_contents_and_instruction(history)

    # Initialize the request body with the user/assistant messages
    body: Dict = {"contents": contents}
    # Include the system-level instruction if present
    if system_inst:
        body["systemInstruction"] = system_inst

    # Construct the SSE endpoint URL with model name and API key
    url = f"{BASE_URL}/{MODEL_NAME}:streamGenerateContent?alt=sse&key={API_KEY}"
    # Prepare headers for JSON body and SSE response
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    # Debug log of the request URL and payload
    logger.debug("STREAM URL: %s", url)
    logger.debug("STREAM BODY: %s", json.dumps(body, ensure_ascii=False, indent=2))

    # Open an HTTPX async client without a timeout to support long-lived streams
    async with httpx.AsyncClient(timeout=None) as client:
        # Initiate a streaming POST request
        async with client.stream("POST", url, headers=headers, json=body) as resp:
            # If the response is not successful, read and log the error, then raise
            if resp.status_code != 200:
                error = (await resp.aread()).decode(errors="ignore")
                logger.error("STREAM error %s: %s", resp.status_code, error)
                raise Exception(f"Google API error {resp.status_code}: {error}")

            # Iterate over each line from the SSE stream
            async for line in resp.aiter_lines():
                # Only process lines that carry data
                if not line.startswith("data: "):
                    continue
                # Strip the "data: " prefix to get the payload
                payload = line[len("data: "):].strip()
                # End streaming when the server signals completion
                if payload == "[DONE]":
                    return
                # Attempt to parse the JSON payload
                try:
                    packet = json.loads(payload)
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
                # Extract and yield each text candidate from the response packet
                for cand in packet.get("candidates", []):
                    text = cand.get("content", {}).get("parts", [{}])[0].get("text")
                    if text:
                        yield text


async def gemini_once(
    prompt: str, session_id: str, history: List[Dict[str, str]]
) -> str:
    """
    Perform a single-shot request to the Google Gemini API generateContent endpoint.

    Args:
        prompt (str): The user’s latest input to send to the model.
        session_id (str): Unique identifier for this conversation session.
        history (List[Dict[str, str]]): Complete conversation history including the new prompt.

    Returns:
        str: The full text response from the model, or an empty string if no content is returned.
    """
    # Assemble the conversation payload from history
    contents, system_inst = _build_contents_and_instruction(history)
    body: Dict = {"contents": contents}
    # Include system instruction if it exists
    if system_inst:
        body["systemInstruction"] = system_inst

    # Construct the request URL for the generateContent endpoint with API key
    url = f"{BASE_URL}/{MODEL_NAME}:generateContent?key={API_KEY}"
    # Set JSON content type header
    headers = {"Content-Type": "application/json"}

    # Perform the HTTP POST request with a reasonable timeout
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=body)

    # If the API returns an error status, read the body, log it, and raise
    if resp.status_code != 200:
        error = (await resp.aread()).decode(errors="ignore")
        logger.error("ONCE error %s: %s", resp.status_code, error)
        raise Exception(f"Google API error {resp.status_code}: {error}")

    # Parse the JSON response payload
    data = resp.json()
    # Extract the text from the first candidate, if available
    for cand in data.get("candidates", []):
        text = cand.get("content", {}).get("parts", [{}])[0].get("text")
        if text:
            return text

    # Return empty string if no candidate text is found
    return ""
