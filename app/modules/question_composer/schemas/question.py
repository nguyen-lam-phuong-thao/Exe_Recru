from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QuestionOption(BaseModel):
    text: str
    value: str

class Question(BaseModel):
    id: str
    text: str
    type: str
    options: Optional[List[QuestionOption]] = None
    required: bool = True
    depends_on: Optional[Dict[str, Any]] = None

class QuestionSet(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    questions: List[Question]

class QuestionComposerResponse(BaseModel):
    question_sets: List[QuestionSet]

class CandidateInput(BaseModel):
    name: str
    skills: List[str]
    mindset: List[str]
    cv_text: str

class GeneratedQuestion(BaseModel):
    question_text: str
    category: str  # e.g., 'skill', 'mindset', 'cv' 