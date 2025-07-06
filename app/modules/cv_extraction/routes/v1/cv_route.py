from fastapi import APIRouter, Depends, Header, File, UploadFile, Form
from app.core.base_model import APIResponse
from app.core.config import FERNET_KEY
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.modules.cv_extraction.repositories.cv_repo import CVRepository

route = APIRouter(prefix='/cv', tags=['CV'])


@route.get("/")
async def root():
    return {"message": "CV API online"}


@route.post('/process', response_model=APIResponse)
async def process_cv(
    cv_file: UploadFile = File(...),
    jd_file: UploadFile = File(...),
    checksum: str = Header(...),
    lang: str = Header('vi'),
    cv_repo: CVRepository = Depends(CVRepository),
):
    """
    Xử lý khi người dùng upload file CV và JD.
    """
    if checksum != FERNET_KEY:
        return APIResponse(error_code=1, message=_('checksum_invalid'), data=None)

    jd_text = (await jd_file.read()).decode('utf-8')
    return await cv_repo.process_uploaded_cv(cv_file, jd_text)


@route.post('/process-url', response_model=APIResponse)
async def process_cv_url(
    cv_file_url: str = Form(...),
    jd_file: UploadFile = File(...),
    checksum: str = Header(...),
    lang: str = Header('vi'),
    cv_repo: CVRepository = Depends(CVRepository),
):
    """
    Xử lý khi người dùng gửi URL của file CV và upload file JD.
    """
    if checksum != FERNET_KEY:
        return APIResponse(error_code=1, message=_('checksum_invalid'), data=None)

    jd_text = (await jd_file.read()).decode('utf-8')

    request = ProcessCVRequest(
        cv_file_url=cv_file_url,
        job_description=jd_text,
    )

    return await cv_repo.process_cv(request)
