# Cấu hình cho workflow job matching

import os
from typing import Optional
from pydantic import BaseModel
from app.core.config import GOOGLE_API_KEY

class JobMatchingWorkflowConfig(BaseModel):
    """Cấu hình cho Job Matching Workflow"""
    
    # LLM Configuration
    llm_model: str = "gemini-2.0-flash"
    max_tokens: int = 2024
    temperature: float = 0.7
    
    # Workflow Configuration
    max_suggested_courses: int = 5
    max_suggested_jobs: int = 5
    max_missing_skills: int = 10
    
    # API Configuration
    google_api_key: str = GOOGLE_API_KEY
    
    @classmethod
    def from_env(cls):
        """Tạo config từ environment variables"""
        return cls(
            llm_model=os.getenv("JOB_MATCHING_LLM_MODEL", "gemini-2.0-flash"),
            max_tokens=int(os.getenv("JOB_MATCHING_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("JOB_MATCHING_TEMPERATURE", "0.7")),
            max_suggested_courses=int(os.getenv("JOB_MATCHING_MAX_COURSES", "5")),
            max_suggested_jobs=int(os.getenv("JOB_MATCHING_MAX_JOBS", "3")),
            max_missing_skills=int(os.getenv("JOB_MATCHING_MAX_SKILLS", "10")),
            google_api_key=GOOGLE_API_KEY,
        )