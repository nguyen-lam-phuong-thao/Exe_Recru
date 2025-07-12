from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.handlers import handle_exceptions
import aiohttp
import logging

from app.modules.job_matching.workflows.matching.schemas.matching import JobMatchingRequest
from app.modules.job_matching.workflows.matching.repository.job_matching_repo import JobMatchingRepo

route = APIRouter(prefix="/job-matching", tags=["Job Matching"])
logger = logging.getLogger(__name__)

@route.post("/suggest", response_model=APIResponse)
@handle_exceptions
async def suggest_job_and_courses(
    request: JobMatchingRequest,
    repo: JobMatchingRepo = Depends(JobMatchingRepo)
) -> APIResponse:
    """
    Gợi ý khóa học và công việc dựa trên JD alignment từ cv_extraction
    
    - Nhận jd_alignment từ API cv_extraction
    - Trích xuất kỹ năng còn thiếu
    - Gợi ý khóa học online để bổ sung kiến thức
    - Gợi ý công việc phù hợp
    - Phân tích lộ trình nghề nghiệp
    """
    return await repo.match_job(request)


async def _call_cv_extraction_api(cv_file: UploadFile, jd_text: str) -> dict:
    """
    Gọi API cv_extraction để phân tích CV
    
    Args:
        cv_file: CV file upload
        jd_text: JD text
        
    Returns:
        Dict chứa kết quả từ cv_extraction
    """
    try:
        # Đọc lại file content
        cv_content = await cv_file.read()
        
        # Gọi API cv_extraction
        async with aiohttp.ClientSession() as session:
            # Tạo form data
            data = aiohttp.FormData()
            data.add_field('file', cv_content, filename=cv_file.filename, content_type=cv_file.content_type)
            data.add_field('jd_file', jd_text.encode('utf-8'), filename='jd.txt', content_type='text/plain')
            
            # Headers
            headers = {
                'checksum': 'your_fernet_key_here'  # Thay bằng key thực tế
            }
            
            # Gọi API
            async with session.post('http://localhost:8000/cv/process', data=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("error_code") == 0:
                        logger.info("CV extraction successful")
                        return result.get("data", {})
                    else:
                        logger.error(f"CV extraction failed: {result.get('message')}")
                        return None
                else:
                    logger.error(f"CV extraction API error: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error calling CV extraction API: {e}")
        return None

@route.get("/status/{session_id}", response_model=APIResponse)
@handle_exceptions
async def get_matching_status(
    session_id: str,
    repo: JobMatchingRepo = Depends(JobMatchingRepo)
) -> APIResponse:
    """
    Lấy trạng thái xử lý của một job matching session
    """
    return await repo.get_matching_status(session_id)

@route.get("/info", response_model=APIResponse)
@handle_exceptions
async def get_service_info(
    repo: JobMatchingRepo = Depends(JobMatchingRepo)
) -> APIResponse:
    """
    Lấy thông tin về Job Matching service
    """
    return repo.get_service_info()

@route.get("/health", response_model=APIResponse)
async def health_check() -> APIResponse:
    """
    Health check endpoint
    """
    return APIResponse(
        error_code=0,
        message=_("service_healthy"),
        data={"status": "healthy", "service": "job_matching"}
    ) 