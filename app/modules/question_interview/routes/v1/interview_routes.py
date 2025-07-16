"""
Question Composer API routes.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends

from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.middleware.translation_manager import _

from ...repository.question_interview_repo import InterviewComposerRepo
from ...schemas.interview_request import (
	SubmitInterviewAnswerRequest,
)

import uuid
from app.exceptions.exception import CustomHTTPException
from app.modules.cv_extraction.repositories.cv_repo import CVRepository
from app.exceptions.handlers import handle_exceptions

# Setup logging
logger = logging.getLogger(__name__)

# Create router - MUST be named 'route'
route = APIRouter(prefix='/question-composer', tags=['Question Composer'])


def get_interview_composer_repo() -> InterviewComposerRepo:
	return InterviewComposerRepo()

@route.post("/start-session", summary="Start interview with CV upload and job description")
@handle_exceptions
async def start_interview_session(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    repo: InterviewComposerRepo = Depends(get_interview_composer_repo),
    cv_repo: CVRepository = Depends(CVRepository),
) -> APIResponse:
	response = await cv_repo.process_uploaded_cv(file, job_description)
	if response.error_code != 0:
		raise CustomHTTPException(message=response.message)

	cleaned_text = response.data['extracted_text']
	session_id = str(uuid.uuid4())
	result = await repo.generate_question_from_cv_text(cleaned_text, job_description, session_id)
	filtered_data = {
		"session_id": result.session_id,
		"questions": result.questions,
		"analysis": result.analysis,
		"next_focus_areas": result.next_focus_areas,
	}

	return APIResponse(error_code=0, message=_("success"), data=filtered_data)

@route.post("/answer", summary="Submit answer and receive feedback")
@handle_exceptions
async def submit_answer_and_get_next_question(
    request: SubmitInterviewAnswerRequest,
    repo: InterviewComposerRepo = Depends(get_interview_composer_repo)
) -> APIResponse:
	feedback = await repo.evaluate_answer_and_continue(request)
	return APIResponse(error_code=0, message=_("success"), data=feedback)

logger.info('Question Composer API routes loaded!')
