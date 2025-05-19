# === app.py ===
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from generator import generate_cv_text, generate_cv_stream

app = FastAPI()

@app.get("/")
def hello():
    return {"message": "✅ CV Generator API is running."}

@app.post("/generate_cv")
async def generate(request: Request):
    user_info = await request.json()
    return generate_cv_text(user_info)

@app.post("/generate_stream")
async def generate_stream(request: Request):
    user_info = await request.json()

    def event_generator():
        for log in generate_cv_stream(user_info):
            yield f"data: {log}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")