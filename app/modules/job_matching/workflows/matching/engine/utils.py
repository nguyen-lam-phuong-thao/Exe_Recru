import json
import re
from typing import Dict, Any


def parse_json_from_response(response: str) -> Dict:
    """Parse JSON từ response của LLM"""
    try:
        parsed_response = json.loads(response)
    except json.JSONDecodeError:
        try:
            # Thử tách code block nếu có
            new_response = response.split('```')[1][5:]
            parsed_response = json.loads(new_response)
        except json.JSONDecodeError:
            # Thử tìm JSON pattern
            pattern = r'(json)\s*({.*})'
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)

            if match:
                parsed_response = json.loads(match.group(2))
            else:
                parsed_response = {}
    return parsed_response


def count_tokens(text: str, model: str = 'gemini-2.0-flash') -> int:
    """Đếm số tokens trong text"""
    if not text:
        return 0

    # Gemini approximates tokens as ~4 characters per token
    if 'gemini' in model.lower():
        return len(text) // 4

    # Fallback for unknown models
    return len(text) // 4


class TokenTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.context_tokens = 0

    @property
    def total_tokens(self):
        return self.input_tokens + self.output_tokens + self.context_tokens

    def add_input_tokens(self, tokens: int):
        self.input_tokens += tokens

    def add_output_tokens(self, tokens: int):
        self.output_tokens += tokens

    def add_context_tokens(self, tokens: int):
        self.context_tokens += tokens

    def reset(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.context_tokens = 0 