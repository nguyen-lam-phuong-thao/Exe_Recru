from fastapi import APIRouter, Body, UploadFile, File, Header, Query, HTTPException
from app.modules.job_matching.repository.matching_service import JobMatchingService
from app.modules.job_matching.schemas.job_matching import MatchingRequest, MatchingResponse, JobResult, CourseResult
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
    Nhận file từ client, forward sang cv_extraction, lưu kết quả và trả về thông báo.
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
            
            # Lấy kết quả từ cv_extraction
            cv_result = response.json()
            
            # Tạo tên file dựa trên tên file CV (loại bỏ extension)
            cv_filename = os.path.splitext(file.filename)[0]
            json_filename = f"{cv_filename}.json"
            
            # Đảm bảo thư mục results tồn tại
            results_dir = "results"
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # Lưu kết quả vào file JSON
            json_file_path = os.path.join(results_dir, json_filename)
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(cv_result, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"Đã lưu kết quả CV vào file: {json_file_path}")
            
            return APIResponse(
                message="Xử lý CV thành công và đã lưu kết quả",
                data={
                    "filename": json_filename,
                    "cv_result": cv_result,
                    "message": f"Kết quả đã được lưu vào file: {json_filename}"
                }
            )
            
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

# @route.get('/result', response_model=APIResponse)
# async def get_cv_result(filename: str = Query(..., description="Tên file CV đã upload (không có extension)")):
#     """
#     Lấy lại kết quả đã xử lý CV dựa vào tên file (hoặc id).
#     """
#     json_path = f"results/{filename}.json"
#     if not os.path.exists(json_path):
#         raise HTTPException(status_code=404, detail="Không tìm thấy kết quả cho file này!")
    
#     try:
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
        
#         return APIResponse(
#             message="Lấy kết quả CV thành công",
#             data={
#                 "filename": f"{filename}.json",
#                 "cv_result": data
#             }
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file kết quả: {str(e)}")

@route.get('/suggest-jobs', response_model=APIResponse)
async def suggest_jobs(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý việc làm phù hợp dựa trên CV đã phân tích.
    """
    # Gợi ý việc làm sử dụng service
    job_suggestions = await job_matching_service.match_jobs(filename)
    
    return APIResponse(
        message="Gợi ý việc làm thành công",
        data={
            "job_suggestions": [job.model_dump() for job in job_suggestions],
            "total_suggestions": len(job_suggestions)
        }
    )

@route.get('/suggest-courses', response_model=APIResponse)
async def suggest_courses(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý khóa học phù hợp dựa trên CV đã phân tích.
    """
    # Gợi ý khóa học sử dụng service
    course_suggestions = await job_matching_service.match_courses(filename)
    
    return APIResponse(
        message="Gợi ý khóa học thành công",
        data={
            "course_suggestions": [course.model_dump() for course in course_suggestions],
            "total_suggestions": len(course_suggestions)
        }
    )

@route.get('/suggest-all', response_model=APIResponse)
async def suggest_all(filename: str = Query(..., description="Tên file CV đã upload")):
    """
    Gợi ý cả việc làm và khóa học dựa trên CV đã phân tích.
    """
    # Gợi ý việc làm và khóa học sử dụng service
    job_suggestions = await job_matching_service.match_jobs(filename)
    course_suggestions = await job_matching_service.match_courses(filename)
    
    return APIResponse(
        message="Gợi ý việc làm và khóa học thành công",
        data={
            "job_suggestions": [job.model_dump() for job in job_suggestions],
            "course_suggestions": [course.model_dump() for course in course_suggestions],
            "total_job_suggestions": len(job_suggestions),
            "total_course_suggestions": len(course_suggestions)
        }
    )

# @route.post('/match', response_model=MatchingResponse)
# async def process_matching(
#     request: MatchingRequest = Body(...),
# ):
#     """
#     Nhận dữ liệu CV và mục tiêu, trả về kết quả matching.
#     """
#     # Giả lập lấy dữ liệu CV (ở đây bạn cần tích hợp thực tế với cv_extraction nếu muốn)
#     cv_data = {"skills": ["Python", "SQL"]}  # TODO: lấy thực tế từ cv_extraction
#     if request.target == "job":
#         jobs = await job_matching_service.match_jobs(cv_data, request.keywords)
#         return MatchingResponse(jobs=jobs)
#     else:
#         courses = await job_matching_service.match_courses(cv_data, request.keywords)
#         return MatchingResponse(courses=courses) 
