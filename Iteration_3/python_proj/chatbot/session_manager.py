import os
import json
from typing import List, Dict

# -----------------------------------------------------------------------------
# Session Storage Directory Setup
# -----------------------------------------------------------------------------
# Define the base directory for storing per-session JSON history files.
dir_base = os.path.join(os.path.dirname(__file__), "User")
# Ensure the directory exists; create it if necessary.
os.makedirs(dir_base, exist_ok=True)

# -----------------------------------------------------------------------------
# System Prompt Loading
# -----------------------------------------------------------------------------
# Load the assistant’s initial system prompt from a text file.
_system_prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(_system_prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_CONTENT = f.read().strip()
# Wrap the system prompt in the standard message format.
SYSTEM_MSG = {"role": "system", "content": SYSTEM_CONTENT}


def _session_path(session_id: str) -> str:
    """
    Construct the file path for storing a session's history JSON.

    Args:
        session_id: Unique identifier for the chat session.

    Returns:
        The full filesystem path to the session's JSON file.
    """
    filename = f"{session_id}.json"
    return os.path.join(dir_base, filename)


def load_history(session_id: str) -> List[Dict[str, str]]:
    """
    Load or initialize the conversation history for a session.

    If no history file exists, create one containing only the system message.
    If the existing file is invalid or empty, reinitialize it.

    Args:
        session_id: Unique identifier for the chat session.

    Returns:
        A list of message dicts, each with 'role' and 'content' keys.
    """
    path = _session_path(session_id)

    # If the session file does not exist, create it with the system prompt.
    if not os.path.isfile(path):
        history = [SYSTEM_MSG]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return history

    # Attempt to read and parse the existing history file.
    try:
        with open(path, 'r', encoding='utf-8') as f:
            history = json.load(f)
        # Ensure the file contains a non-empty list of messages.
        if isinstance(history, list) and history:
            return history
    except Exception:
        # Fall through to reinitialization on any read/parse error.
        pass

    # On error or invalid content, reinitialize the file with system prompt.
    history = [SYSTEM_MSG]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return history


def save_history(session_id: str, role: str, content: str) -> None:
    """
    Append a new message to the session history and persist to disk.

    Args:
        session_id: Unique identifier for the chat session.
        role: Sender role, either 'user' or 'assistant'.
        content: Text content of the message.
    """
    path = _session_path(session_id)
    # Load current history (will recreate file if missing).
    history = load_history(session_id)
    # Append the new message dict.
    history.append({"role": role, "content": content})
    # Overwrite the history file with the updated list.
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def reset_history(session_id: str) -> None:
    """
    Reset conversation history for one or all sessions.

    If session_id == "all", delete every JSON file in the User directory.
    Otherwise, delete the file for the given session_id. On failure,
    recreate the session file initialized with only the system message.

    Args:
        session_id: Session identifier or "all" for a full reset.
    """
    # Full reset: remove all session files.
    if session_id == "all":
        for filename in os.listdir(dir_base):
            if filename.endswith('.json'):
                try:
                    os.remove(os.path.join(dir_base, filename))
                except Exception:
                    # Ignore individual file deletion errors.
                    continue
        return

    # Single-session reset: delete or reinitialize the specific file.
    path = _session_path(session_id)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except Exception:
            # On deletion failure, overwrite with only the system message.
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([SYSTEM_MSG], f, ensure_ascii=False, indent=2)
    else:
        # If file does not exist, create it with only the system message.
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([SYSTEM_MSG], f, ensure_ascii=False, indent=2)
