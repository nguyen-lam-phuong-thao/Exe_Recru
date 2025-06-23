from typing import List, Optional
from datetime import date
from pydantic import BaseModel, EmailStr, field_validator

from app.core.base_model import RequestSchema

class ProcessCVRequest(RequestSchema):
	cv_file_url: str

# Sub-schemas
class EducationEntry(BaseModel):
    degree: str
    institution: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class ExperienceEntry(BaseModel):
    title: str
    company: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class ProjectEntry(BaseModel):
    title: str
    tech_stack: List[str]
    description: Optional[str] = None

    class Config:
        orm_mode = True

class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    time_period: Optional[date] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

# Main schemas
class CVBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    summary: Optional[str] = None
    education: List[EducationEntry]
    experience: List[ExperienceEntry]
    skills: List[str]
    projects: Optional[List[ProjectEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None

    class Config:
        orm_mode = True

class CVCreate(CVBase):
    uploaded_by: str
    source: str  # e.g., 'manual', 'email', 'ATS', etc.

    class Config:
        orm_mode = True

class CVResponse(CVBase):
    id: str
    created_at: date
    updated_at: date

    class Config:
        orm_mode = True 