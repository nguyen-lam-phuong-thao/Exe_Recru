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
    company: Optional[str] = None
    location: Optional[str] = None
    match_score: Optional[int] = None
    required_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None

class CourseResult(BaseModel):
    course_name: str
    title: str
    description: str
    provider: Optional[str] = None
    duration: Optional[str] = None
    match_score: Optional[int] = None
    skills_covered: Optional[List[str]] = None

class MatchingResponse(BaseModel):
    jobs: Optional[List[JobResult]] = None
    courses: Optional[List[CourseResult]] = None