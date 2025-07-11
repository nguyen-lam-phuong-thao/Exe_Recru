import logging
from typing import Dict, Any

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.modules.job_matching.workflows.matching.engine.job_matching_agent import JobMatchingAgent
from app.modules.job_matching.workflows.matching.config.workflow_config import JobMatchingWorkflowConfig
from app.modules.job_matching.workflows.matching.schemas.matching import (
    JobMatchingRequest, 
    JobMatchingResponse,
    JobMatchingState
)

logger = logging.getLogger(__name__)

class JobMatchingRepo:
    """Repository layer cho job matching module"""
    
    def __init__(self):
        logger.info('Initializing JobMatchingRepo')
        
        # Khởi tạo config và agent
        self.config = JobMatchingWorkflowConfig.from_env()
        self.agent = JobMatchingAgent(self.config)
        
        logger.info('JobMatchingRepo initialized successfully')
    
    async def match_job(self, request: JobMatchingRequest) -> APIResponse:
        """
        Xử lý job matching request - nhận dữ liệu từ cv_extraction và sinh gợi ý
        
        Args:
            request: JobMatchingRequest chứa jd_alignment và cv_analysis_result từ cv_extraction
            
        Returns:
            APIResponse với các gợi ý khóa học, công việc và phân tích lộ trình
        """
        logger.info(f'Starting job matching for request: {request}')
        
        try:
            # Gọi agent để xử lý - nhận dữ liệu từ cv_extraction
            result: Dict[str, Any] = await self.agent.process_job_matching(
                jd_alignment=request.jd_alignment,
                cv_analysis_result=request.cv_analysis_result
            )
            
            # Kiểm tra kết quả
            if result.get('processing_status') == "error":
                logger.error(f"Job matching failed: {result.get('error_message')}")
                return APIResponse(
                    error_code=1,
                    message=_("job_matching_failed"),
                    data=None
                )
            
            # Tạo response từ kết quả
            response = JobMatchingResponse(
                missing_skills=result.get('missing_skills', []),
                suggested_courses=result.get('suggested_courses', []),
                suggested_jobs=result.get('suggested_jobs', []),
                career_path_analysis=result.get('career_path_analysis', {}),
                analysis_timestamp=result.get('analysis_timestamp'),
                session_id=result.get('session_id'),
                processing_status=result.get('processing_status')
            )
            
            logger.info(f'Job matching completed successfully. '
                       f'Found {len(result.get("missing_skills", []))} missing skills, '
                       f'{len(result.get("suggested_courses", []))} courses, '
                       f'{len(result.get("suggested_jobs", []))} jobs')
            
            return APIResponse(
                error_code=0,
                message=_("job_matching_successful"),
                data=response.dict()
            )
            
        except Exception as e:
            logger.error(f'Error in job matching: {str(e)}')
            return APIResponse(
                error_code=1,
                message=_("job_matching_error"),
                data=None
            )
    
    async def get_matching_status(self, session_id: str) -> APIResponse:
        """
        Lấy trạng thái xử lý của một session
        
        Args:
            session_id: ID của session cần kiểm tra
            
        Returns:
            APIResponse chứa thông tin trạng thái
        """
        try:
            # Lấy state từ memory
            state = await self.agent.memory.get({"configurable": {"thread_id": session_id}})
            
            if state:
                status_data = {
                    "session_id": session_id,
                    "status": state.get("processing_status", "unknown"),
                    "error_message": state.get("error_message"),
                    "progress": {
                        "skills_extracted": len(state.get("missing_skills", [])),
                        "courses_suggested": len(state.get("suggested_courses", [])),
                        "jobs_suggested": len(state.get("suggested_jobs", [])),
                        "career_path_analyzed": state.get("career_path_analysis") is not None
                    }
                }
                return APIResponse(
                    error_code=0,
                    message=_("status_retrieved_successfully"),
                    data=status_data
                )
            else:
                return APIResponse(
                    error_code=1,
                    message=_("session_not_found"),
                    data={
                        "session_id": session_id,
                        "status": "not_found",
                        "error_message": "Session not found"
                    }
                )
            
        except Exception as e:
            logger.error(f'Error getting matching status: {str(e)}')
            return APIResponse(
                error_code=1,
                message=_("status_retrieval_failed"),
                data={
                    "session_id": session_id,
                    "status": "error",
                    "error_message": str(e)
                }
            )
    
    def get_service_info(self) -> APIResponse:
        """Lấy thông tin service"""
        service_info = {
            "service_name": "Job Matching Service",
            "version": "1.0.0",
            "config": {
                "llm_model": self.config.llm_model,
                "max_suggested_courses": self.config.max_suggested_courses,
                "max_suggested_jobs": self.config.max_suggested_jobs,
                "max_missing_skills": self.config.max_missing_skills
            },
            "workflow_nodes": [
                "extract_missing_skills",
                "suggest_courses", 
                "suggest_jobs",
                "analyze_career_path"
            ]
        }
        
        return APIResponse(
            error_code=0,
            message=_("service_info_retrieved"),
            data=service_info
        ) 