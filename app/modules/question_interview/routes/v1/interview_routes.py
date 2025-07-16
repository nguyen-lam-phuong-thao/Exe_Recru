"""
Question Composer API routes.
"""

import logging
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.exceptions.handlers import handle_exceptions

from ...repository.question_interview_repo import InterviewComposerRepo
from ...schemas.interview_request import SubmitInterviewAnswerRequest
from app.modules.cv_extraction.repositories.cv_repo import CVRepository
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest

# Setup logging
logger = logging.getLogger(__name__)

# Create router - MUST be named 'route'
route = APIRouter(prefix='/question-composer', tags=['Question Composer'])


def get_interview_composer_repo() -> InterviewComposerRepo:
    return InterviewComposerRepo()


def get_cv_repo() -> CVRepository:
    return CVRepository()


@route.post("/start-session", summary="Start interview session with uploaded CV file")
@handle_exceptions
async def start_interview_session_with_file(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    repo: InterviewComposerRepo = Depends(get_interview_composer_repo),
    cv_repo: CVRepository = Depends(get_cv_repo),
) -> APIResponse:
    """
    Bắt đầu phiên phỏng vấn với CV được upload dưới dạng file.
    """
    response = await cv_repo.process_uploaded_cv(file, job_description)

    if response.error_code != 0:
        raise CustomHTTPException(message=response.message)

    cleaned_text = response.data.get('extracted_text')
    if not cleaned_text:
        raise CustomHTTPException(message="CV text extraction failed.")

    session_id = str(uuid.uuid4())
    result = await repo.generate_question_from_cv_text(cleaned_text, job_description, session_id)

    filtered_data = {
        "session_id": result.session_id,
        "questions": result.questions,
        "analysis": result.analysis,
        "next_focus_areas": result.next_focus_areas,
    }

    return APIResponse(error_code=0, message=_("success"), data=filtered_data)


@route.post("/start-session-url", summary="Start interview session with CV file URL")
@handle_exceptions
async def start_interview_session_with_url(
    cv_file_url: str = Form(...),
    job_description: str = Form(...),
    repo: InterviewComposerRepo = Depends(get_interview_composer_repo),
    cv_repo: CVRepository = Depends(get_cv_repo),
) -> APIResponse:
    """
    Bắt đầu phiên phỏng vấn với đường dẫn URL tới file CV.
    """
    request = ProcessCVRequest(
        cv_file_url=cv_file_url,
        job_description=job_description,
    )
    response = await cv_repo.process_cv(request)

    if response.error_code != 0:
        raise CustomHTTPException(message=response.message)

    cleaned_text = response.data.get('extracted_text')
    if not cleaned_text:
        raise CustomHTTPException(message="CV text extraction failed.")

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
    repo: InterviewComposerRepo = Depends(get_interview_composer_repo),
) -> APIResponse:
    """
    Gửi câu trả lời phỏng vấn và nhận phản hồi.
    """
    feedback = await repo.evaluate_answer_and_continue(request)
    return APIResponse(error_code=0, message=_("success"), data=feedback)


logger.info('Question Composer API routes loaded!')

