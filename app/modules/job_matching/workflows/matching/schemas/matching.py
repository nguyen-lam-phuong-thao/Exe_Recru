from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

# Request/Response Schemas
class JobMatchingRequest(BaseModel):
    """Request schema cho job matching"""
    jd_alignment: str = Field(..., description="Kết quả đánh giá JD alignment từ cv_extraction")
    cv_analysis_result: Optional[Dict[str, Any]] = Field(None, description="Toàn bộ kết quả phân tích CV (optional)")

class CourseSuggestion(BaseModel):
    """Schema cho gợi ý khóa học"""
    course_name: str = Field(..., description="Tên khóa học")
    platform: str = Field(..., description="Nền tảng (Coursera, Udemy, edX, etc.)")
    description: str = Field(..., description="Mô tả khóa học")
    estimated_duration: str = Field(..., description="Thời gian ước tính")
    url: Optional[str] = Field(None, description="Link khóa học")

class JobSuggestion(BaseModel):
    """Schema cho gợi ý công việc"""
    job_title: str = Field(..., description="Tên vị trí công việc")
    company_name: str = Field(..., description="Tên công ty phù hợp")
    required_skills: List[str] = Field(..., description="Kỹ năng yêu cầu")
    salary_range: str = Field(..., description="Mức lương ước tính")
    description: str = Field(..., description="Mô tả công việc")
    url: Optional[str] = Field(None, description="Link bài đăng tuyển dụng hoặc khóa họchọc")

class CareerPathAnalysis(BaseModel):
    """Schema cho phân tích lộ trình nghề nghiệp"""
    career_path: str = Field(..., description="Lộ trình nghề nghiệp đề xuất")
    short_term_goals: List[str] = Field(..., description="Mục tiêu ngắn hạn")
    long_term_goals: List[str] = Field(..., description="Mục tiêu dài hạn")
    priority_skills: List[str] = Field(..., description="Kỹ năng ưu tiên học trước")
    estimated_timeline: str = Field(..., description="Thời gian ước tính")

class JobMatchingResponse(BaseModel):
    """Response schema cho job matching - nhận dữ liệu từ cv_extraction và sinh gợi ý"""
    missing_skills: List[str] = Field(..., description="Danh sách kỹ năng còn thiếu")
    suggested_courses: List[CourseSuggestion] = Field(..., description="Danh sách khóa học gợi ý")
    suggested_jobs: List[JobSuggestion] = Field(..., description="Danh sách công việc gợi ý")
    career_path_analysis: Optional[Dict[str, Any]] = Field(None, description="Phân tích lộ trình nghề nghiệp")
    analysis_timestamp: Optional[datetime] = Field(None, description="Thời gian phân tích")
    session_id: Optional[str] = Field(None, description="Session ID")
    processing_status: Optional[str] = Field(None, description="Trạng thái xử lý")

# LangGraph State Schemas
class JobMatchingState(BaseModel):
    """State schema cho LangGraph workflow"""
    # Input data
    jd_alignment: str = Field(..., description="JD alignment từ cv_extraction")
    cv_analysis_result: Optional[Dict[str, Any]] = Field(None, description="CV analysis result")
    
    # Processing results
    missing_skills: List[str] = Field(default_factory=list, description="Kỹ năng còn thiếu")
    suggested_courses: List[CourseSuggestion] = Field(default_factory=list, description="Khóa học gợi ý")
    suggested_jobs: List[JobSuggestion] = Field(default_factory=list, description="Công việc gợi ý")
    career_path_analysis: Optional[CareerPathAnalysis] = Field(None, description="Phân tích lộ trình")
    
    # Workflow metadata
    session_id: str = Field(..., description="Session ID")
    processing_status: str = Field(default="pending", description="Trạng thái xử lý")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi nếu có")
    
    # LLM usage tracking
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage tracking") 