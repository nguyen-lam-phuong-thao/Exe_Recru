"""
Interview request schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from app.core.base_model import RequestSchema, FilterableRequestSchema


class UploadCVInterviewStartRequest(RequestSchema):
    job_description: str = Field(..., description="The job position text used to tailor the interview.")

class AnalyzeUserProfileRequest(RequestSchema):
	"""Request for analyzing user profile completeness"""

	user_profile: Dict[str, Any] = Field(..., description='User profile data to analyze')


class GetQuestionSessionRequest(RequestSchema):
	"""Request for getting question session"""

	session_id: str = Field(..., description='Session ID to retrieve')


class SearchQuestionSessionsRequest(FilterableRequestSchema):
	"""Request for searching question sessions with filtering"""

	user_id: Optional[str] = Field(None, description='Filter by user ID')
	status: Optional[str] = Field(None, description='Filter by session status')
	session_id: Optional[str] = Field(None, description='Filter by session ID')


class SubmitInterviewAnswerRequest(RequestSchema):
    """Request to submit an answer for evaluation."""
    session_id: str = Field(..., description="Current interview session ID")
    question_id: str = Field(..., description="ID of the question being answered")
    answer_text: str = Field(..., description="User's answer to the last question")
    # Optionally, allow previous_questions for more context if needed
    previous_questions: Optional[list] = Field(None, description="List of previous questions and answers for context")
