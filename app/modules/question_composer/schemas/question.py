from pydantic import BaseModel
from typing import List

class CandidateInput(BaseModel):
    name: str
    skills: List[str]
    mindset: List[str]
    cv_text: str

class GeneratedQuestion(BaseModel):
    question_text: str
    category: str  # e.g., 'skill', 'mindset', 'cv' 