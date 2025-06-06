from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from generator import generate_cv_text, generate_cv_stream

# Instantiate the FastAPI application with metadata
app = FastAPI(
    title="CV Generator API",
    description="API for generating CV text synchronously or via server-sent events stream.",
    version="1.0.0"
)

@app.get("/", tags=["health"])
def hello():
    """
    Health check endpoint.
    Returns a JSON message confirming that the API is operational.
    """
    return {"message": "✅ CV Generator API is running."}

@app.post("/generate_cv", tags=["generation"])
async def generate(request: Request):
    """
    Synchronous CV generation endpoint.
    Expects:
      - request.json(): a dict containing user information.
    Returns:
      - A complete CV text generated by the `generate_cv_text` function.
    """
    # Parse the incoming JSON payload into a Python dict
    user_info = await request.json()
    # Delegate CV text generation to the synchronous generator function
    return generate_cv_text(user_info)

@app.post("/generate_stream", tags=["generation", "stream"])
async def generate_stream(request: Request):
    """
    Streaming CV generation endpoint using Server-Sent Events (SSE).
    Expects:
      - request.json(): a dict containing user information.
    Streams:
      - Progressive log messages from `generate_cv_stream`.
    """
    # Parse incoming JSON payload into a Python dict
    user_info = await request.json()

    def event_generator():
        """
        Internal generator function that yields CV generation logs
        formatted as SSE data events.
        """
        # Iterate over each log message from the streaming generator
        for log in generate_cv_stream(user_info):
            # Send each log as an SSE data event
            yield f"data: {log}\n\n"
        # Signal completion of the stream to the client
        yield "data: [DONE]\n\n"

    # Return a StreamingResponse with the required media type for SSE
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
