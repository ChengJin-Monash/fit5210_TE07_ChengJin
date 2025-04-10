# fit5210_TE07_ChengJin
AI part for FIT5210 TE07 IE project


# 🧠 CV Generator API (FastAPI + LLaMA.cpp)

A lightweight, local LLM-powered CV generator API using **FastAPI** and **llama.cpp** (via [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)). This project allows structured CV data (e.g., name, education, work experience) to be submitted via API, and returns well-formatted personal descriptions for professional resumes.

---

## 📁 Project Structure

```
.
├── app.py                   # Main FastAPI app with streaming and non-streaming endpoints
├── app.py_nostream          # Variant of the app without SSE streaming
├── generator.py             # Core CV generation logic using LLaMA model
├── generator.py_nostream    # Variant without streaming support
├── prompt_builder.py        # Prompt construction module for profile, education, and work
├── cv_output.txt            # Last generated CV saved as plain text
├── prompts/                 # Auto-saved raw prompts used for debugging
├── __pycache__/             # Python bytecode cache
```

---

## 🚀 Features

- ✅ **Profile, Education, and Work Experience generation** using local LLM
- 🧩 Modular design with prompt builders per section
- 🔁 **Streaming support** via Server-Sent Events (`/generate_stream`)
- 📝 Clean and editable CV output saved as `cv_output.txt`
- 🔍 Saved prompt debugging via `prompts/`

---

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install fastapi uvicorn llama-cpp-python
```

### 2. Prepare Your Model

Download and place your `.gguf` model (e.g., `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`) under the path:

```
/home/azureuser/tinyllama1b/models/
```

Update the path in `generator.py` if needed:

```python
model_path = os.path.expanduser("your_path_to_model.gguf")
```

---

## 🧪 API Endpoints

### `POST /generate_cv`

Generates a CV and returns a JSON response with all generated sections.

**Request Body:**
```json
{
  "name": "Alice Zhang",
  "education": [
    {
      "degree_type": "Bachelor",
      "degree_name": "Computer Science",
      "institution": "Monash University",
      "year_start": "2019",
      "year_end": "2022"
    }
  ],
  "work_experience": [
    {
      "job_title": "Software Engineer",
      "organization": "Google",
      "year_start": "2023",
      "year_end": "2025"
    }
  ]
}
```

**Response:**
```json
{
  "cv_heading": "...",
  "profile_heading": "...",
  "profile_content": "...",
  "education_heading": "...",
  "education_list": [...],
  "education_content": "...",
  "experience_heading": "...",
  "experience_list": [...],
  "experience_content": "..."
}
```

---

### `POST /generate_stream`

Same input format as `/generate_cv`, but streams logs in real-time using **Server-Sent Events (SSE)**.

**Use case**: For frontend UIs that want to show real-time "Generating..." logs.

---

## 🧠 How It Works

1. User submits structured info (name, education, work).
2. `prompt_builder.py` builds prompts for:
   - Personal profile
   - Education history
   - Work experience
3. Prompts are passed to `llama.cpp` for generation using `generator.py`.
4. Output is cleaned and trimmed to natural sentences.
5. Result is assembled, returned, and saved to `cv_output.txt`.

---

## 📌 Notes

- The model is loaded once globally for performance.
- Token budget is dynamically computed based on input length.
- Prompts are saved under `prompts/` folder for debug or fine-tuning inspection.

---

## 📦 Run the API

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs) for Swagger API docs.

---

## 📜 License

MIT License © 2025
