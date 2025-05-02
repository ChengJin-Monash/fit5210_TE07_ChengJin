from llama_cpp import Llama
import os

# ===================== 全局配置 =====================
CONFIG = {
    "MODEL_PATH": os.path.abspath("/home/azureuser/tinyllama1b/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),
    "SYSTEM_PROMPT_PATH": os.path.abspath("./system_prompt.txt"),
    "N_CTX": 2048,
    "N_THREADS": 6,
    "MAX_TOKENS": 512,
    "TEMPERATURE": 0.7
}

# ===================== 模型初始化 =====================
def init_model():
    llm = Llama(
        model_path=CONFIG["MODEL_PATH"],
        n_ctx=CONFIG["N_CTX"],
        n_threads=CONFIG["N_THREADS"]
    )
    return llm

# ===================== 默认 system prompt 加载函数 =====================
def get_default_system_prompt():
    with open(CONFIG["SYSTEM_PROMPT_PATH"], "r", encoding="utf-8") as f:
        return f.read()

# ===================== 流式输出函数 =====================
def chat_stream(llm, messages: list[dict]):
    stream = llm.create_chat_completion(
        messages=messages,
        stream=True,
        max_tokens=CONFIG["MAX_TOKENS"],
        temperature=CONFIG["TEMPERATURE"]
    )
    for chunk in stream:
        content = chunk["choices"][0]["delta"].get("content")
        if content:
            yield content


def chat_once(llm, messages: list[dict]) -> str:
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=CONFIG["MAX_TOKENS"],
        temperature=CONFIG["TEMPERATURE"]
    )
    return response["choices"][0]["message"]["content"]
