# Job Matching Module
from .schemas import MatchingRequest, MatchingResponse, JobResult, CourseResult
from .prompts import JOB_SUGGESTION_PROMPT, COURSE_SUGGESTION_PROMPT
from .repository.matching_service import JobMatchingService

__all__ = [
    "MatchingRequest",
    "MatchingResponse", 
    "JobResult",
    "CourseResult",
    "JOB_SUGGESTION_PROMPT",
    "COURSE_SUGGESTION_PROMPT",
    "JobMatchingService"
]
