"""
Question schemas following the frontend question API structure.
"""

from typing import List, Optional, Union, Any, Dict, Literal
from pydantic import BaseModel, Field

class TextInputField(BaseModel):
	"""Text input field configuration"""

	id: str = Field(..., description='Unique identifier for the field')
	label: str = Field(..., description='Display label for the field')
	type: str = Field(..., description='Input type (text, email, tel, etc.)')
	placeholder: str = Field(..., description='Placeholder text')
	required: bool = Field(default=True, description='Whether field is required')


class Question(BaseModel):
	"""A question using only text_input type."""

	id: str = Field(..., description='Unique identifier for the question')
	Question: str = Field(..., description='The main question text')
	Question_type: Literal['text_input'] = Field(..., description='Type of question (fixed to text_input)')
	subtitle: Optional[str] = Field(None, description='Optional subtitle or helper text')
	Question_data: List[TextInputField] = Field(..., description='List of text input fields')
	answer: Optional[str] = Field(None, description="User's answer to this question")

class UserProfile(BaseModel):
	"""User profile structure for analysis"""

	current_role: Optional[str] = Field(None, description='Current professional role')
	skills: List[str] = Field(default_factory=list, description='Technical skills')
	interests: List[str] = Field(default_factory=list, description='Areas of interest')
	goals: List[str] = Field(default_factory=list, description='Professional goals')
	experience_level: Optional[str] = Field(None, description='Experience level')
	industry: Optional[str] = Field(None, description='Industry')
	personal_info: Dict[str, Any] = Field(default_factory=dict, description='Personal information')
	additional_info: Dict[str, Any] = Field(default_factory=dict, description='Additional user data')


class QuestionGenerationRequest(BaseModel):
	"""Request for generating questions"""

	# cv_data: Optional[UserProfile] = Field(None, description='Existing user profile data')
	previous_questions: List[Question] = Field(default_factory=list, description='Previously asked questions')
	focus_areas: List[str] = Field(default_factory=list, description='Specific areas to focus on')
	max_questions: int = Field(4, description='Maximum number of questions to generate')
	questions: List[Question]
	analysis: str
	next_focus_areas: List[str]
	completeness_score: float
	should_continue: bool
	session_id: Optional[str] = Field(None, description="Session ID for back-and-forth interview flow")  # ✅
	current_iteration: Optional[int] = 0
	total_questions_generated: Optional[int] = 0


class QuestionGenerationResponse(BaseModel):
	"""Response containing generated questions"""

	questions: List[Question] = Field(..., description='Generated questions')
	analysis: str = Field(..., description='Analysis of user profile completeness')
	next_focus_areas: List[str] = Field(..., description='Areas that need more information')
	completeness_score: float = Field(..., description='User profile completeness score (0-1)')
	should_continue: bool = Field(..., description='Whether more questions are needed')


class AnalysisDecision(BaseModel):
	"""Decision from analysis node"""

	decision: Literal['sufficient', 'need_more_info'] = Field(..., description='Whether user information is sufficient')
	missing_areas: List[str] = Field(default_factory=list, description='Areas that need more information')
	reasoning: str = Field(..., description='Reasoning for the decision')
	completeness_score: float = Field(..., description='User profile completeness score (0-1)')
	suggested_focus: List[str] = Field(default_factory=list, description='Suggested areas to focus on next')
	cv_summary: Optional[str] = None  # ✅ New field

class SubmitInterviewAnswerRequest(BaseModel):
    """Schema for submitting answer to current question"""

    session_id: str = Field(..., description="Current interview session ID")
    answer_text: str = Field(..., description="User's answer to the last question")


