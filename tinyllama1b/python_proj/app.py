# === app.py ===

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from generator import generate_cv_text, generate_cv_stream

# Initialize FastAPI application
app = FastAPI()

@app.get("/")
def hello():
    """
    Health check endpoint to confirm the API is running.
    Returns a simple JSON message.
    """
    return {"message": "✅ CV Generator API is running."}

@app.post("/generate_cv")
async def generate(request: Request):
    """
    Endpoint to generate a complete CV text based on user input.
    
    Parameters:
        request (Request): The incoming POST request with JSON-formatted user info.
        
    Returns:
        dict: A dictionary containing the generated CV text.
    """
    user_info = await request.json()
    return generate_cv_text(user_info)

@app.post("/generate_stream")
async def generate_stream(request: Request):
    """
    Endpoint to generate a CV via server-sent events (SSE) streaming.

    This allows streaming the CV generation process line-by-line,
    which is useful for showing progress in real-time on the frontend.

    Parameters:
        request (Request): The incoming POST request with JSON-formatted user info.

    Returns:
        StreamingResponse: A text/event-stream response that yields generated content.
    """
    user_info = await request.json()

    def event_generator():
        """
        Generator function that yields each line of the generated CV
        in the format required for SSE (Server-Sent Events).
        """
        for log in generate_cv_stream(user_info):
            yield f"data: {log}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
