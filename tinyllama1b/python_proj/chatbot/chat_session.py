import os
import json
from typing import List, Dict

# 会话保存路径
USER_SESSION_DIR = "./user"

class ChatSession:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def append_user(self, message: str):
        self.history.append({"role": "user", "content": message})

    def append_assistant(self, message: str):
        self.history.append({"role": "assistant", "content": message})

    def get_messages(self) -> List[Dict[str, str]]:
        return self.history

    def save_to_file(self, user_id: str):
        folder = os.path.join(USER_SESSION_DIR, user_id)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{user_id}_chatsession.txt")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    @staticmethod
    def load_from_file(user_id: str, system_prompt: str):
        folder = os.path.join(USER_SESSION_DIR, user_id)
        path = os.path.join(folder, f"{user_id}_chatsession.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f)
            session = ChatSession(system_prompt)
            session.history = history
            return session
        else:
            return ChatSession(system_prompt)
