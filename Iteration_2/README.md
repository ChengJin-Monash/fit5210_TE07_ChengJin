
# 🧠 TinyLLaMA-Powered CV & Chatbot APIs

This repository provides two AI-driven microservices built with **FastAPI** and **llama.cpp**, using local LLaMA-compatible models (GGUF format). These tools are optimized for deployment in resource-efficient environments (such as virtual machines on Azure) without depending on third-party APIs or internet connectivity.

---

## 📌 Project Purpose

This project addresses the needs of mature-age job seekers (e.g., aged 50–65) by offering two intelligent features:

1. **CV Generator API** – Automatically builds professional resume text from structured data, enabling non-technical users to create clean and confident self-presentations.
2. **Chatbot API** – Offers personalized, context-aware guidance on job-seeking, re-skilling, and addressing common concerns (e.g., employment gaps).

Both services prioritize data privacy, local control, and transparent AI behavior by operating fully offline with TinyLLaMA.

---

## 🧱 Architecture Overview

```
[User Input]
     ↓
[FastAPI Endpoint]
     ↓
[Prompt Builder] -- [System Prompt (Chatbot)] or [Sectional Prompts (CV)]
     ↓
[TinyLLaMA Inference via llama.cpp]
     ↓
[Post-processor: Clean-up, SSE Streaming (if enabled)]
     ↓
[Response Output or CV Text File]
```

Each module (CV and Chatbot) is designed to be independently deployable, yet they share a similar pattern of prompt → inference → response.

---

## 📁 Full Directory Layout

```
tinyllama1b/
├── models/                         # Place GGUF models here
│   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
│
├── python_proj/
│   ├── chatbot/                    # Chatbot module
│   │   ├── main.py                 # FastAPI app for /chatbot
│   │   ├── chat_session.py         # Maintains conversational context
│   │   ├── tiny_runner.py          # Low-level llama.cpp integration
│   │   ├── system_prompt.txt       # Instruction prompt (role: career advisor)
│   │   ├── cmds.txt                # Optional command list
│   │   └── test_stream.html        # Frontend test tool (SSE enabled)
│   │
│   ├── cv_builder/                 # CV generator module
│   │   ├── main.py                 # FastAPI app for /generate_cv and /stream
│   │   ├── generator.py            # Core logic using llama inference
│   │   ├── prompt_builder.py       # Builds section-based prompts
│   │   ├── cv_output.txt           # Logs final generated CV
│   │   └── prompts/
│   │       ├── profile_prompt.txt
│   │       ├── edu_prompt.txt
│   │       └── work_prompt.txt
│   │
│   ├── requirements.txt
│   ├── cmdlog.sh                   # CLI shortcut for testing
│   └── __pycache__/
│
├── server_setup.sh                 # Bash script for Azure deployment
└── testing.sh                      # Batch tester or launcher
```

---

## ✍️ CV Builder API

### What It Does
- Accepts user input (name, education, work history)
- Builds modular prompts for each section
- Calls TinyLLaMA to generate text responses for each part
- Returns structured JSON or streams each part via SSE
- Saves final result to `cv_output.txt`

### Key Files
- `cv_builder/main.py` – FastAPI app routes
- `prompt_builder.py` – Constructs full prompt dynamically
- `generator.py` – Calls llama model and handles response

### How to Run
```bash
cd tinyllama1b/python_proj/cv_builder
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoints
- `POST /generate_cv` – Full output in JSON
- `POST /generate_stream` – Line-by-line streaming output

---

## 💬 Chatbot API

### What It Does
- Accepts a question about job seeking (career planning, interview prep, etc.)
- Combines it with `system_prompt.txt` to stay on-topic
- Stores short session history in memory
- Responds using TinyLLaMA (Tiny Runner wrapper)

### Key Files
- `chatbot/main.py` – FastAPI app
- `chat_session.py` – Keeps prior exchanges
- `system_prompt.txt` – Defines tone, role, context

### How to Run
```bash
cd tinyllama1b/python_proj/chatbot
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Endpoint
- `POST /chatbot` – Input: `{ "question": "..." }` → Output: `{ "response": "..." }`

---

## 🧠 Model Integration & Optimization

- Model is loaded once per service on startup
- Uses `llama-cpp-python` backend for TinyLLaMA (GGUF format)
- Prompt + context is dynamically sized to stay within token limits
- No GPU dependency (runs well on CPU with quantized model)

---

## 🧪 Testing & Debugging

### For CV Builder
```bash
curl -X POST http://localhost:8000/generate_cv -H "Content-Type: application/json" -d @test_cv.json
```

### For Chatbot
```bash
curl -X POST http://localhost:8001/chatbot -H "Content-Type: application/json" -d '{"question": "What skills should I learn to return to work?"}'
```

### HTML Debug Page
- `chatbot/test_stream.html` – Open in browser to test SSE streaming

---

## 📦 Installation

```bash
cd tinyllama1b/python_proj
pip install -r requirements.txt
```

Place your `.gguf` model under `tinyllama1b/models/` and update paths in `generator.py` or `tiny_runner.py` as needed.

---

## 🔐 Privacy & Deployment Notes

- Runs entirely offline — no API calls are made to external services
- Best hosted on secure VM (e.g., Azure Ubuntu server with port 8000/8001)
- Logging only saved locally for debugging (no persistent storage)

---

## 📜 License

MIT License © 2025
