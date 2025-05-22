from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.core.base_model import APIResponse

class UserCharacteristicsInput(BaseModel):
    """
    Schema for user characteristics input.
    Accepts any unstructured JSON data.
    """
    data: Dict[str, Any] = Field(..., description="Unstructured JSON data representing user characteristics.")

class GeneratedQuestion(BaseModel):
    """
    Schema for a single generated question.
    """
    id: str = Field(..., description="Unique identifier for the question.")
    text: str = Field(..., description="The text of the question.")
    category: str = Field(default="general", description="Category of the question.")
    # Add other relevant fields like relevance_score, type, etc. as needed

class QuestionCompositionResponseData(BaseModel):
    """
    Data part of the response for question composition.
    """
    questions: List[GeneratedQuestion] = Field(..., description="List of generated critical questions.")

class QuestionCompositionAPIResponse(APIResponse):
    """
    API response schema for question composition.
    """
    data: QuestionCompositionResponseData | None = None
