import os
import json
from typing import List, Dict

# Base directory for storing per-user chat session files
USER_SESSION_DIR = "./user"

class ChatSession:
    """
    Manage a single user's chat session, including in-memory history
    and persistence to disk.
    """
    def __init__(self, system_prompt: str):
        """
        Initialize a new ChatSession.

        Args:
            system_prompt (str): The initial system message to seed the history.
        """
        self.system_prompt = system_prompt
        # Begin history with the system prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def append_user(self, message: str):
        """
        Add a user message to the session history.

        Args:
            message (str): The text content of the user's message.
        """
        self.history.append({"role": "user", "content": message})

    def append_assistant(self, message: str):
        """
        Add an assistant message to the session history.

        Args:
            message (str): The text content of the assistant's reply.
        """
        self.history.append({"role": "assistant", "content": message})

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retrieve the full conversation history.

        Returns:
            List[Dict[str, str]]: List of messages, each with 'role' and 'content'.
        """
        return self.history

    def save_to_file(self, user_id: str):
        """
        Persist the session history to a JSON file on disk.

        The history is written under USER_SESSION_DIR/user_id/user_id_chatsession.txt.

        Args:
            user_id (str): Unique identifier for this user's session.
        """
        folder = os.path.join(USER_SESSION_DIR, user_id)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{user_id}_chatsession.txt")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_from_file(user_id: str, system_prompt: str):
        """
        Load a ChatSession from disk, or create a new one if none exists.

        If a session file exists, its contents populate the history.
        Otherwise, a fresh session seeded with the system prompt is returned.

        Args:
            user_id (str): Unique identifier for the user's session.
            system_prompt (str): System message to initialize new sessions.

        Returns:
            ChatSession: The loaded or newly created session instance.
        """
        folder = os.path.join(USER_SESSION_DIR, user_id)
        path = os.path.join(folder, f"{user_id}_chatsession.txt")

        # Load and return existing session if available
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f)
            session = ChatSession(system_prompt)
            session.history = history
            return session

        # No existing file: return a new session with only system prompt
        return ChatSession(system_prompt)
