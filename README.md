# Iteration 3 README

## Table of Contents
1. [Project Overview](#project-overview)
2. [New Features & Enhancements](#new-features--enhancements)
3. [System Architecture](#system-architecture)
4. [Directory Structure](#directory-structure)
5. [Configuration Management](#configuration-management)
6. [Installation & Setup](#installation--setup)
7. [Running the Services](#running-the-services)
8. [API Endpoints](#api-endpoints)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Contributing](#contributing)
12. [License](#license)

---

## Project Overview
Iteration 3 enhances our dual microservice platform by integrating Google Gemini alongside TinyLLaMA for natural language generation. This update streamlines code, centralizes configuration, and introduces robust session management and reset capabilities. Both the **CV Builder API** and **Chatbot API** now support multi-model invocation and improved performance.

## New Features & Enhancements
- **Multi-Model Support**: Toggle between local TinyLLaMA (GGUF) and Google Gemini models for richer, context-aware outputs.
- **Centralized Configuration**: All paths, keys, ports, and generation parameters are defined in `chatbot_config.py` or environment variables.
- **Advanced Session Management**: Replaced `chat_session.py` with `session_manager.py` to persist, load, and reset user histories stored under `python_proj/chatbot/User/`.
- **Session Reset Utility**: `chat_reset.sh` script calls the `/chat_reset` endpoint to clear one or all sessions for testing and maintenance.
- **Runner Refactor**: `tinyllama_runner.py` caches model instances to reduce initialization overhead and unifies streaming vs. batch inference logic.
- **CV Builder Simplification**: Retained a single `generator.py` for resume construction, discarding legacy experimental files for maintainability. Logs outputs to `cv_output.txt`.
- **Dependency Management**: Added `requirements.txt` at project root and within each submodule for reproducible environments.

## System Architecture
```
+-----------------+        +-------------------+
|  Client / UI    |  <-->  |   FastAPI Layer   |
+-----------------+        +---+-----------+---+
                                  |           |
                    +-------------+           +--------------+
                    |                                     |
            +-------v--------+                   +--------v--------+
            | Chatbot API    |                   | CV Builder API  |
            | (Port 8001)    |                   | (Port 8000)     |
            +-------+--------+                   +--------+--------+
                    |                                     |
    +---------------+------+                  +-----------+-------+
    |                      |                  |                   |
+---v-------------+  +-----v-------------+  +---v-------------+  +--v-------------+
| session_manager |  | gemini_runner     |  | prompt_builder |  | tinyllama_runner |
| & storage       |  | tinyllama_runner  |  | (CV sections)  |  | (TinyLLaMA GGUF) |
+-----------------+  +-------------------+  +----------------+  +-----------------+
```

## Directory Structure
```
.
├── README.md
├── requirements.txt               # Root dependencies
├── server_setup.sh                # Environment bootstrap script
├── testing.sh                     # Bulk API testing utility
│
└── python_proj/
    ├── chatbot/                   # Chatbot Microservice
    │   ├── main.py                # FastAPI app entrypoint (/chatbot)
    │   ├── chatbot_config.py      # Centralized settings & API keys
    │   ├── session_manager.py     # Load/save/reset user sessions
    │   ├── tinyllama_runner.py    # Local model inference wrapper
    │   ├── gemini_runner.py       # Google Gemini API wrapper
    │   ├── system_prompt.txt      # System prompt template
    │   ├── User/                  # Stored JSON session histories
    │   └── chat_reset.sh          # Script to invoke /chat_reset endpoint
    │
    └── cv_builder/                # Resume Generation Microservice
        ├── requirements.txt       # CV-specific dependencies
        ├── main.py                # FastAPI app entrypoint (/generate_cv)
        ├── prompt_builder.py      # Build profile/edu/work prompts
        ├── generator.py           # Unified TinyLLaMA invocation
        ├── prompts/               # Text templates for CV sections
        │   ├── profile_prompt.txt
        │   ├── edu_prompt.txt
        │   └── work_prompt.txt
        └── cv_output.txt          # Log of generated CV outputs
```

## Configuration Management
- **chatbot_config.py**: Defines model paths, ports (`CHATBOT_PORT`, `CV_PORT`), API keys, token limits, and toggle flags for model selection.
- **Environment Variables**: Override defaults for sensitive data (e.g., `GOOGLE_API_KEY`, `MODEL_PATH`, `LOG_LEVEL`).
- **requirements.txt**: Lists pinned versions of all Python dependencies for consistent deployment.


## Installation & Setup
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd project-root
   ```
2. Review server_setup.sh: 
    This file contains a sequence of shell commands used to configure an Ubuntu VM and install dependencies; 
    it serves as an operation record rather than a fully automated installer.
3. (Optional) Activate your Python virtual environment and install local dependencies:
   ```bash
   cd python_proj/chatbot
   pip install -r requirements.txt
   cd ../cv_builder
   pip install -r requirements.txt
   ```

## Running the Services
- **CV Builder** (port default `8000`):
  ```bash
  cd python_proj/cv_builder
  uvicorn main:app --host 0.0.0.0 --port ${CV_PORT:-8000} --reload
  ```
- **Chatbot** (port default `8001`):
  ```bash
  cd python_proj/chatbot
  uvicorn main:app --host 0.0.0.0 --port ${CHATBOT_PORT:-8001} --reload
  ```

## API Endpoints

### Chatbot Service
| Method | Endpoint          | Description                                    |
|--------|-------------------|------------------------------------------------|
| POST   | `/chat`           | Send user message + history, returns response  |
| POST   | `/chat_stream`    | SSE stream of chatbot response                 |
| POST   | `/chat_reset`     | Reset one or all sessions (body: `{id:...}`)   |

### CV Builder Service
| Method | Endpoint            | Description                                    |
|--------|---------------------|------------------------------------------------|
| POST   | `/generate_cv`      | Generate full CV in one request                |
| POST   | `/generate_stream`  | SSE stream of CV generation by sections        |

## Testing
1. Review `testing.sh`: this file documents the individual shell commands needed to test each API endpoint; it is provided as an operation log rather than a turnkey test script.  
2. Run the commands listed in `testing.sh` manually (copy-paste or source them in your shell).  
3. Inspect the `logs/` directory (populated by those commands) for detailed success/failure summaries.

## Deployment
1. Ensure `.env` contains appropriate values for keys and ports.
2. Use `docker-compose` or Kubernetes manifests (to be added) for production-grade deployment.
3. Monitor logs and resource usage; scale `uvicorn` workers as needed.

## Contributing
1. Fork the repository and create a feature branch.
2. Follow project code style and add tests for new functionality.
3. Open a Pull Request with a clear description of your changes.

## License
Distributed under the MIT License. See `LICENSE` for details.
