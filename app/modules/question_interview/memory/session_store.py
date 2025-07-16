# question_interview/memory/session_store.py

import json
from pathlib import Path
import os

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


def save_session_state(session_id: str, state: dict):
    session_file = SESSIONS_DIR / f"{session_id}.json"


    def convert(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj

    cleaned_state = convert(state)

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_state, f, ensure_ascii=False, indent=2)

def load_session_state(session_id: str) -> dict:
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return {}
    with open(session_file, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_session_state(session_id: str):
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

