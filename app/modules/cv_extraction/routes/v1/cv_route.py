from fastapi import APIRouter, Depends, Header, File, UploadFile, Form

from app.core.base_model import APIResponse
from app.core.config import FERNET_KEY
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.modules.cv_extraction.repositories.cv_repo import CVRepository


route = APIRouter(prefix='/cv', tags=['CV'])


@route.get('/')
async def get_user_info():
	"""
	Lấy thông tin người dùng hiện tại.
	"""
	return {'message': 'User information retrieved successfully.'}


@route.post('/process', response_model=APIResponse)
async def process_cv(
	file: UploadFile = File(...),
	jd_file: UploadFile = File(...),
	checksum: str = Header(...),
	cv_repo: CVRepository = Depends(CVRepository),
):
	"""
	Xử lý file CV từ URL.
	"""
	# Validate checksum

	if checksum != FERNET_KEY:
		return APIResponse(
			error_code=1,
			message=_('checksum_invalid'),
			data=None,
		)

	# Read JD text if provided
	jd_text = (await jd_file.read()).decode('utf-8')

	return await cv_repo.process_uploaded_cv(file, job_description=jd_text)
