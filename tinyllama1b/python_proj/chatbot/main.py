from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from tiny_runner import init_model, get_default_system_prompt, chat_stream as stream_response_generator
from chat_session import ChatSession
import uvicorn
import shutil
import os

# 初始化 FastAPI 应用
app = FastAPI()

# 加载模型（仅一次）
llm = init_model()

# 会话存储（运行时内存）
session_store: dict[str, ChatSession] = {}

# 请求体定义（不再需要 system_prompt 字段）
class ChatRequest(BaseModel):
    prompt: str
    session_id: str

class SessionResetRequest(BaseModel):
    session_id: str

@app.post("/chat_session")
def chat_with_session(request: ChatRequest):
    # 如果是新会话，则初始化 ChatSession，加载本地的 system_prompt.txt
    if request.session_id not in session_store:
        system_prompt = get_default_system_prompt()
        session_store[request.session_id] = ChatSession(system_prompt)

    session = session_store[request.session_id]
    session.append_user(request.prompt)

    response = llm.create_chat_completion(
        messages=session.get_messages(),
        max_tokens=512,
        temperature=0.7
    )
    reply = response["choices"][0]["message"]["content"]
    session.append_assistant(reply)
    session.save_to_file(request.session_id)

    return {"response": reply}


@app.post("/chat_stream_reset")
def reset_session(request: SessionResetRequest):
    base_path = os.path.join("user", request.session_id)

    if request.session_id == "all":
        session_store.clear()
        user_base = "user"
        if os.path.exists(user_base):
            for entry in os.listdir(user_base):
                entry_path = os.path.join(user_base, entry)
                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
        return {
            "status": "ok",
            "message": "All sessions have been reset."
        }

    if request.session_id in session_store:
        del session_store[request.session_id]

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


@app.post("/chat_stream")
def chat_stream(request: ChatRequest):
    if request.session_id not in session_store:
        system_prompt = get_default_system_prompt()
        session_store[request.session_id] = ChatSession(system_prompt)

    session = session_store[request.session_id]
    session.append_user(request.prompt)

    def event_stream():
        full_reply = ""
        for chunk in stream_response_generator(llm, session.get_messages()):
            full_reply += chunk
            yield f"data: {chunk}\n\n"

        # ✅ 修复关键：生成完整后更新 session 记录
        session.append_assistant(full_reply)
        session.save_to_file(request.session_id)
        yield "data: ✅ Chat complete\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# 本地运行入口（可选）
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
