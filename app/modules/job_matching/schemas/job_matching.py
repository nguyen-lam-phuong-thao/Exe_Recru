from pydantic import BaseModel
from typing import List, Optional

class MatchingRequest(BaseModel):
    cv_id: str
    target: str  # "job" hoặc "course"
    keywords: Optional[List[str]] = None

class JobResult(BaseModel):
    job_id: str
    title: str
    description: str

class CourseResult(BaseModel):
    course_id: str
    title: str
    description: str

class MatchingResponse(BaseModel):
    jobs: Optional[List[JobResult]] = None
    courses: Optional[List[CourseResult]] = None