import os
import shutil
import uvicorn

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tiny_runner import (
    init_model,
    get_default_system_prompt,
    chat_stream as stream_response_generator
)
from chat_session import ChatSession

# -----------------------------------------------------------------------------
# Application Initialization
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Still-Skilled Chatbot Service",
    version="1.0.0"
)

# Load and cache the language model once at startup
llm = init_model()

# In-memory store for active ChatSession instances, keyed by session_id
session_store: dict[str, ChatSession] = {}

# -----------------------------------------------------------------------------
# Request Body Schemas
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    """
    Schema for chat requests.
    - prompt: The user's input text.
    - session_id: Unique identifier for the chat session.
    """
    prompt: str
    session_id: str

class SessionResetRequest(BaseModel):
    """
    Schema for session reset requests.
    - session_id: Identifier of the session to reset ('all' for global reset).
    """
    session_id: str

# -----------------------------------------------------------------------------
# Endpoint: /chat_session
# -----------------------------------------------------------------------------
@app.post("/chat_session")
def chat_with_session(request: ChatRequest):
    """
    Handle a blocking single-turn chat interaction.
    - Initializes a new ChatSession if not already present.
    - Appends user message to history.
    - Sends all messages to the LLM for a one-shot completion.
    - Appends assistant reply to history and persists to file.
    """
    # Initialize session on first use
    if request.session_id not in session_store:
        system_prompt = get_default_system_prompt()
        session_store[request.session_id] = ChatSession(system_prompt)

    session = session_store[request.session_id]
    session.append_user(request.prompt)

    # Perform a one-shot completion
    response = llm.create_chat_completion(
        messages=session.get_messages(),
        max_tokens=512,
        temperature=0.7
    )
    reply = response["choices"][0]["message"]["content"]

    # Save assistant response in session history and persist
    session.append_assistant(reply)
    session.save_to_file(request.session_id)

    return {"response": reply}

# -----------------------------------------------------------------------------
# Endpoint: /chat_stream_reset
# -----------------------------------------------------------------------------
@app.post("/chat_stream_reset")
def reset_session(request: SessionResetRequest):
    """
    Reset conversation history for one or all sessions.
    - If session_id == "all": clears in-memory store and deletes all user folders.
    - Otherwise: removes the specific session from memory and deletes its files.
    """
    # Handle global reset of all sessions
    if request.session_id == "all":
        session_store.clear()
        user_base = USER_SESSION_DIR = "user"
        if os.path.exists(user_base):
            for entry in os.listdir(user_base):
                entry_path = os.path.join(user_base, entry)
                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
        return {
            "status": "ok",
            "message": "All sessions have been reset."
        }

    # Remove specific session from in-memory store
    if request.session_id in session_store:
        del session_store[request.session_id]

    # Delete the session folder on disk if it exists
    base_path = os.path.join("user", request.session_id)
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        return {
            "status": "ok",
            "message": f"Session '{request.session_id}' has been reset (memory and file)."
        }
    else:
        return {
            "status": "ok",
            "message": f"Session '{request.session_id}' reset from memory only (no local file)."
        }

# -----------------------------------------------------------------------------
# Endpoint: /chat_stream
# -----------------------------------------------------------------------------
@app.post("/chat_stream")
def chat_stream(request: ChatRequest):
    """
    Handle streaming chat via Server-Sent Events (SSE).
    - Initializes a new ChatSession if not present.
    - Appends user message to history.
    - Uses stream_response_generator to yield token chunks.
    - After full response, appends assistant reply and persists history.
    """
    # Initialize session on first use
    if request.session_id not in session_store:
        system_prompt = get_default_system_prompt()
        session_store[request.session_id] = ChatSession(system_prompt)

    session = session_store[request.session_id]
    session.append_user(request.prompt)

    def event_stream():
        """
        Generator function yielding SSE-formatted token chunks.
        After streaming completes, updates session history with the full reply.
        """
        full_reply = ""
        for chunk in stream_response_generator(llm, session.get_messages()):
            full_reply += chunk
            # SSE protocol: prefix each data chunk
            yield f"data: {chunk}\n\n"

        # After completion, save the assembled assistant message
        session.append_assistant(full_reply)
        session.save_to_file(request.session_id)
        # Send a final marker to signal completion to the client
        yield "data: ✅ Chat complete\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# -----------------------------------------------------------------------------
# Application Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Run the app locally for development/testing.
    """
    uvicorn.run("main:app", host="0.0.0.0", port=8000)