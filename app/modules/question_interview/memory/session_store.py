import os
import json
import tempfile
from typing import Dict

# Tạo dictionary lưu mapping session_id -> temp file path
TEMP_SESSION_FILES: Dict[str, str] = {}

def save_session_state(session_id: str, state: dict):
    def convert(obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj

    cleaned_state = convert(state)

    if session_id not in TEMP_SESSION_FILES:
        # Tạo file tạm và lưu đường dẫn
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        TEMP_SESSION_FILES[session_id] = tmp_file.name
        tmp_file.close()  # Đóng ngay để có thể mở lại ghi dữ liệu

    session_file = TEMP_SESSION_FILES[session_id]
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_state, f, ensure_ascii=False, indent=2)

def load_session_state(session_id: str) -> dict:
    session_file = TEMP_SESSION_FILES.get(session_id)
    if not session_file or not os.path.exists(session_file):
        return {}
    with open(session_file, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_session_state(session_id: str):
    session_file = TEMP_SESSION_FILES.pop(session_id, None)
    if session_file and os.path.exists(session_file):
        os.remove(session_file)
