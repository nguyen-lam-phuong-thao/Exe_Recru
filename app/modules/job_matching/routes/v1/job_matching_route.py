from fastapi import APIRouter, Body, UploadFile, File, Header, Query, HTTPException
from app.modules.job_matching.repository.matching_service import JobMatchingService
from app.modules.job_matching.schemas.job_matching import MatchingRequest, MatchingResponse
import httpx
from app.core.base_model import APIResponse
import json
import os

route = APIRouter(prefix='/job-matching', tags=['Job Matching'])

# Khởi tạo service
job_matching_service = JobMatchingService()

@route.post('/job_matching/get_info')
async def get_result_cv_extraction(
    file: UploadFile = File(...),
    jd_file: UploadFile = File(...),
    checksum: str = Header(...)
):
    """
    Nhận file từ client, forward sang cv_extraction, trả về nguyên response body.
    """
    file_bytes = await file.read()
    jd_bytes = await jd_file.read()

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:  # Tăng timeout lên 5 phút
            files = {
                "file": (file.filename, file_bytes, file.content_type),
                "jd_file": (jd_file.filename, jd_bytes, jd_file.content_type),
            }
            headers = {"checksum": checksum}
            response = await client.post(
                "http://127.0.0.1:8000/api/v1/cv/process",
                files=files,
                headers=headers
            )
            return response.json()
    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=408, 
            detail="CV processing timeout. Please try again or check if the CV file is too large."
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Error connecting to CV processing service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error during CV processing: {str(e)}"
        )

# @route.get('/result', response_model=dict)
# async def get_cv_result(filename: str = Query(..., description="Tên file CV đã upload")):
#     """
#     Lấy lại kết quả đã xử lý CV dựa vào tên file (hoặc id).
#     """
#     json_path = f"results/{filename}.json"
#     if not os.path.exists(json_path):
#         raise HTTPException(status_code=404, detail="Không tìm thấy kết quả cho file này!")
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     return data

@route.get('/suggest-jobs')
async def suggest_jobs(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý việc làm phù hợp dựa trên CV đã phân tích.
    """
    # Gợi ý việc làm sử dụng service
    job_suggestions = await job_matching_service.match_jobs(filename)
    
    return {
        "message": "Gợi ý việc làm thành công",
        "data": {
            "job_suggestions": job_suggestions,
            "total_suggestions": len(job_suggestions)
        }
    }

@route.get('/suggest-courses')
async def suggest_courses(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý khóa học phù hợp dựa trên CV đã phân tích.
    """
    # Gợi ý khóa học sử dụng service
    course_suggestions = await job_matching_service.match_courses(filename)
    
    return {
        "message": "Gợi ý khóa học thành công",
        "data": {
            "course_suggestions": course_suggestions,
            "total_suggestions": len(course_suggestions)
        }
    }

@route.get('/suggest-all')
async def suggest_all(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý cả việc làm và khóa học dựa trên CV đã phân tích.
    """
    # Gợi ý việc làm và khóa học sử dụng service
    job_suggestions = await job_matching_service.match_jobs(filename)
    course_suggestions = await job_matching_service.match_courses(filename)
    
    return {
        "message": "Gợi ý việc làm và khóa học thành công",
        "data": {
            "job_suggestions": job_suggestions,
            "course_suggestions": course_suggestions,
            "total_job_suggestions": len(job_suggestions),
            "total_course_suggestions": len(course_suggestions)
        }
    }

@route.post('/match', response_model=MatchingResponse)
async def process_matching(
    request: MatchingRequest = Body(...),
):
    """
    Nhận dữ liệu CV và mục tiêu, trả về kết quả matching.
    """
    # Giả lập lấy dữ liệu CV (ở đây bạn cần tích hợp thực tế với cv_extraction nếu muốn)
    cv_data = {"skills": ["Python", "SQL"]}  # TODO: lấy thực tế từ cv_extraction
    if request.target == "job":
        jobs = await job_matching_service.match_jobs(cv_data, request.keywords)
        return MatchingResponse(jobs=jobs)
    else:
        courses = await job_matching_service.match_courses(cv_data, request.keywords)
        return MatchingResponse(courses=courses) 
