import os
import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from gemini_runner import gemini_stream, gemini_once
from tinyllama_runner import tinyllama_stream, tinyllama_once
from session_manager import load_history, save_history, reset_history

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
# Retrieve the desired log level from the environment variable "LOG_LEVEL";
# default to "INFO" if not set. Convert to uppercase to match logging constants.
default_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Initialize the root logger with a basic configuration:
# - level: determined by default_level (or INFO if invalid)
# - format: timestamp, logger name, severity level, and message
# - datefmt: readable date/time format
logging.basicConfig(level=getattr(logging, default_level, logging.INFO))

# Create a module-specific logger for internal logging within this file.
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# FastAPI Application Setup
# -----------------------------------------------------------------------------
# Instantiate the FastAPI application, providing metadata for
# automatic API documentation (Swagger UI, Redoc).
app = FastAPI(
    title="Still-Skilled Chatbot Service",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# CORS Middleware (Development/Testing Only)
# -----------------------------------------------------------------------------
# Enable Cross-Origin Resource Sharing (CORS) to allow the API to be
# called from web clients hosted on different origins during development.
# WARNING: In production, restrict origins, methods, and headers to improve
# security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat_stream")
async def chat_stream(request: Request):
    """
    Handle streaming chat responses via Server-Sent Events (SSE).
    Expects a JSON payload with 'session_id' and 'prompt' fields.
    Streams tokens from the configured language model and persists conversation history.
    """
    # Parse JSON body from incoming POST request
    payload = await request.json()
    session_id = payload.get("session_id")
    prompt = payload.get("prompt", "")

    # Validate required fields: both session_id and prompt must be provided
    if not session_id or not prompt:
        logger.warning("Missing session_id or prompt in request")
        # Return HTTP 400 Bad Request if validation fails
        raise HTTPException(status_code=400, detail="Missing session_id or prompt")

    # Log the received prompt for this session
    logger.info(f"Session {session_id}: Received prompt: {prompt}")

    # Load existing conversation history for context
    history = load_history(session_id)
    # Append user message to history immediately
    save_history(session_id, "user", prompt)
    # Reload history to include the newly saved user prompt
    history = load_history(session_id)
    logger.debug(f"Session {session_id}: History length: {len(history)} messages")

    async def event_generator():
        """
        Asynchronous generator yielding model tokens as they arrive.
        First attempts to stream from Gemini API; on failure, falls back to TinyLLaMA.
        After streaming completes, saves the full assistant response to history.
        """
        assistant_buffer = []


        # Attempt streaming response from the remote Gemini API
        try:
            logger.info(f"Session {session_id}: Attempting to use Gemini API")
            async for token in gemini_stream(prompt, session_id, history):
                logger.debug(f"Session {session_id}: Gemini token chunk: {token!r}")
                assistant_buffer.append(token)
                yield token  # Push each token to the client in real time

            # Combine all token chunks into the full assistant response  
            full_response = "".join(assistant_buffer)
            save_history(session_id, "assistant", full_response)
            logger.info(f"Session {session_id}: Gemini response saved (length {len(full_response)})")
            return  # End generator after successful streaming

        except Exception as e:
            # Log any errors from the Gemini API and clear buffer for fallback
            logger.error(f"Session {session_id}: Gemini stream error: {e}")
            assistant_buffer.clear()

        # Fallback: stream response from the local TinyLLaMA instance
        logger.info(f"Session {session_id}: Falling back to TinyLLaMA streaming")
        async for token in tinyllama_stream(prompt, session_id, history):
            logger.debug(f"Session {session_id}: TinyLLaMA token chunk: {token!r}")
            assistant_buffer.append(token)
            yield token  # Stream tokens to the client

        # Save the complete fallback response once streaming finishes
        full_response = "".join(assistant_buffer)
        save_history(session_id, "assistant", full_response)
        logger.info(f"Session {session_id}: TinyLLaMA response saved (length {len(full_response)})")

    # Return an SSE response that will invoke the event_generator
    return EventSourceResponse(event_generator())


@app.post("/chat_once")
async def chat_once(payload: dict):
    """
    Handle a single-turn chat request.
    Expects a JSON payload with 'session_id' and 'prompt'.
    Returns the complete assistant response in one message.
    """
    # Extract session identifier and user prompt from the request payload
    session_id = payload.get("session_id")
    prompt = payload.get("prompt", "")

    # Validate that both session_id and prompt are provided
    if not session_id or not prompt:
        logger.warning("Missing session_id or prompt in chat_once request")
        # Respond with HTTP 400 Bad Request on validation failure
        raise HTTPException(status_code=400, detail="Missing session_id or prompt")

    # Log the received prompt for this session
    logger.info(f"Session {session_id}: chat_once prompt: {prompt}")

    # Load existing conversation history for context
    history = load_history(session_id)
    # Save the user's message to the history immediately
    save_history(session_id, "user", prompt)
    # Reload history to include the newly saved prompt
    history = load_history(session_id)
    logger.debug(f"Session {session_id}: History messages: {len(history)}")

    try:
        # Attempt a single-shot response from the remote Gemini API
        logger.info(f"Session {session_id}: Calling gemini_once")
        response_text = await gemini_once(prompt, session_id, history)
        logger.info(f"Session {session_id}: Received Gemini once response (length {len(response_text)})")
    except Exception as e:
        # On failure, log the error and fall back to the local TinyLLaMA model
        logger.error(f"Session {session_id}: Gemini once failed: {e}")
        logger.info(f"Session {session_id}: Falling back to tinyllama_once")
        response_text = await tinyllama_once(prompt, session_id, history)
        logger.info(f"Session {session_id}: Received TinyLLaMA once response (length {len(response_text)})")

    # Save the assistant's reply to conversation history
    save_history(session_id, "assistant", response_text)
    logger.info(f"Session {session_id}: chat_once response saved")

    # Return the full assistant response as JSON
    return {"response": response_text}


@app.post("/chat_reset")
async def chat_reset(payload: dict):
    session_id = payload.get("session_id")
    if not session_id:
        logger.warning("Missing session_id in chat_reset request")
        raise HTTPException(status_code=400, detail="Missing session_id")
    reset_history(session_id)
    logger.info(f"Session {session_id}: History reset")
    return {"status": "reset"}

# Reset single session or all sessions when session_id == "all"
@app.post("/chat_reset")
async def chat_reset(payload: dict):
    """
    Reset the conversation history for a given session.
    Expects a JSON payload with the 'session_id' field.
    Returns a simple JSON status confirmation upon success.
    """
    # Extract the session identifier from the request payload
    session_id = payload.get("session_id")

    # Validate that the session_id is provided
    if not session_id:
        logger.warning("Missing session_id in chat_reset request")
        # Respond with HTTP 400 Bad Request if validation fails
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    # Perform the history reset operation for this session
    reset_history(session_id)
    logger.info(f"Session {session_id}: History reset")

    # Return a confirmation of the reset action
    return {"status": "reset"}


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
# Define a lightweight endpoint for external systems (load balancers, orchestrators,
# monitoring tools) to verify that the service is up and running.
@app.get("/health")
async def health_check():
    """
    GET /health
    ---
    A basic health check endpoint that returns a minimal JSON payload indicating
    the API is operational. Useful for readiness and liveness probes.
    
    Returns:
        dict: A JSON object with a single key 'status' set to 'ok' when healthy.
    """
    # Immediately return a success status; no dependencies or database checks performed here.
    return {"status": "ok"}
