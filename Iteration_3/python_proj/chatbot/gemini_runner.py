import os
import json
import logging
import httpx
from typing import AsyncGenerator, List, Dict, Tuple

from session_manager import load_history, save_history

# Create a module-specific logger for diagnostic and audit messages.
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# System Prompt Loading
# -----------------------------------------------------------------------------
# The system prompt establishes the assistant’s persona, instructions, and
# any initial context required by the language model on each invocation.
# It is read once at module import time to avoid repeated file I/O.
dir_base = os.path.dirname(__file__)
_SYSTEM_PROMPT_PATH = os.path.join(dir_base, "system_prompt.txt")
with open(_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

# Load multiple API keys from file, one per line
google_key_file = os.path.join(dir_base, "google_api_key.txt")
with open(google_key_file, "r", encoding="utf-8") as f:
    API_KEYS = [line.strip() for line in f if line.strip()]

# Helper to get model endpoint URL for a given key
def _make_url(stream: bool, api_key: str) -> str:
    endpoint = "streamGenerateContent" if stream else "generateContent"
    params = "?alt=sse&key=" + api_key if stream else "?key=" + api_key
    return f"{os.getenv('BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models')}/{os.getenv('MODEL_NAME', 'gemini-1.5-flash')}:{endpoint}{params}"


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
            contents.append({"role": role, "parts": [{"text": text}]})
    
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
    body = {"contents": contents}
    # Include the system-level instruction if present
    if system_inst:
        body["systemInstruction"] = system_inst

    # Try each API key in sequence
    for api_key in API_KEYS:
        url = _make_url(True, api_key)
        # Prepare headers for JSON body and SSE response
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}

        # Debug log of the request URL and payload
        logger.debug(f"Trying key {api_key}, STREAM URL: {url}")
        try:
            # Open an HTTPX async client without a timeout to support long-lived streams
            async with httpx.AsyncClient(timeout=None) as client:

                # Initiate a streaming POST request
                async with client.stream("POST", url, headers=headers, json=body) as resp:

                    # If the response is not successful, read and log the error, then raise
                    if resp.status_code != 200:
                        raise httpx.HTTPStatusError(f"Status {resp.status_code}", request=resp.request, response=resp)
                    
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
                        packet = json.loads(payload)

                        # Extract and yield each text candidate from the response packet
                        for cand in packet.get("candidates", []):
                            text = cand.get("content", {}).get("parts", [{}])[0].get("text")
                            if text:
                                yield text
            return
        except Exception as e:
            logger.warning(f"API key {api_key} failed for stream: {e}")
            continue
    raise Exception("All API keys failed for streaming")


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
    body = {"contents": contents}
    # Include system instruction if it exists
    if system_inst:
        body["systemInstruction"] = system_inst

    for api_key in API_KEYS:
        # Construct the request URL for the generateContent endpoint with API key
        url = _make_url(False, api_key)
        # Set JSON content type header
        headers = {"Content-Type": "application/json"}
        logger.debug(f"Trying key {api_key}, ONCE URL: {url}")
        try:
            # Perform the HTTP POST request with a reasonable timeout
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=body)
            
            # If the API returns an error status, read the body, log it, and raise
            if resp.status_code != 200:
                raise httpx.HTTPStatusError(f"Status {resp.status_code}", request=resp.request, response=resp)
            
            # Parse the JSON response payload
            data = resp.json()
            # Extract the text from the first candidate, if available
            candidates = data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                if text:
                    return text
        except Exception as e:
            logger.warning(f"API key {api_key} failed for once: {e}")
            continue
    raise Exception("All API keys failed for one-shot generation")
