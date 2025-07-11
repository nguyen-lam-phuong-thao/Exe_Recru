from fastapi import APIRouter, Depends, Header, File, UploadFile, Form
from app.core.base_model import APIResponse
from app.core.config import FERNET_KEY
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.modules.cv_extraction.repositories.cv_repo import CVRepository
from charset_normalizer import from_bytes  

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

    # Read JD text if provided
    jd_bytes = await jd_file.read()

    # Detect encoding and convert to UTF-8
    detection = from_bytes(jd_bytes).best()
    if not detection:
        return APIResponse(
            error_code=1,
            message=_("Không thể xác định mã hóa văn bản của file JD."),
            data=None,
        )

    jd_text = detection.output()
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

    # Read JD text if provided
    jd_bytes = await jd_file.read()

    # Detect encoding and convert to UTF-8
    detection = from_bytes(jd_bytes).best()
    if not detection:
        return APIResponse(
            error_code=1,
            message=_("Không thể xác định mã hóa văn bản của file JD."),
            data=None,
        )

    jd_text = detection.output()

    request = ProcessCVRequest(
        cv_file_url=cv_file_url,
        job_description=jd_text,
    )

    return await cv_repo.process_cv(request)