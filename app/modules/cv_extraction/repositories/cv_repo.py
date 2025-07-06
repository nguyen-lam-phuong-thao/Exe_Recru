import aiohttp
import aiofiles
import uuid
import os
import logging
from fastapi import File, UploadFile
import tempfile
import shutil
from typing import Optional
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.modules.cv_extraction.repositories.cv_agent import CVAnalyzer
from app.modules.cv_extraction.repositories.cv_agent.ai_to_api_mapper import ai_to_cvbase
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.utils.pdf import PDFToTextConverter

class CVRepository:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_uploaded_cv(self, file: UploadFile, job_description: Optional[str] = None) -> APIResponse:
        self.logger.info(f"Processing uploaded file: {file.filename}")
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension not in ['pdf', 'docx', 'txt']:
            return APIResponse(error_code=1, message=_('unsupported_cv_file_type'), data=None)

        try:
            suffix = f".{file_extension}"
            async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_path = tmp.name
                contents = await file.read()
                await tmp.write(contents)
            self.logger.info(f"Saved uploaded file to {temp_path}")
        except Exception as e:
            self.logger.error(f"Failed to save file: {e}")
            return APIResponse(error_code=1, message=_('failed_to_save_uploaded_file'), data=None)

        extracted_text = None
        converter = None

        try:
            if file_extension == 'pdf':
                converter = PDFToTextConverter(file_path=temp_path)
                extracted_text = converter.extract_text()
                self.logger.info(f"Extracted {len(extracted_text.get('text', ''))} characters from PDF")
            else:
                return APIResponse(error_code=1, message=_('unsupported_cv_file_type'), data=None)
        except Exception as e:
            self.logger.error(f"Extraction error: {e}")
            return APIResponse(error_code=1, message=_('error_extracting_cv_content'), data=None)
        finally:
            if converter:
                converter.close()
            if os.path.exists(temp_path):
                os.remove(temp_path)

        if not extracted_text or not extracted_text.get('text'):
            return APIResponse(error_code=1, message=_('no_text_extracted'), data=None)

        try:
            cv_analyzer = CVAnalyzer()
            ai_result = await cv_analyzer.analyze_cv_content(extracted_text['text'], job_description)
            if ai_result is None:
                return APIResponse(error_code=1, message=_('error_analyzing_cv'), data=None)
            mapped_result = ai_to_cvbase(ai_result)
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return APIResponse(error_code=1, message=_('error_analyzing_cv'), data=None)

        return APIResponse(
            error_code=0,
            message=_('cv_processed_successfully'),
            data={
                'filename': file.filename,
                'extracted_text': extracted_text['text'],
                'cv_analysis_result': mapped_result.dict(),
                'jd_alignment': getattr(ai_result, "alignment_with_jd", None),
            },
        )

    async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
        self.logger.info(f"Processing CV from URL: {request.cv_file_url}")
        file_path = await self._download_file(request.cv_file_url)

        if not file_path:
            return APIResponse(error_code=1, message=_('failed_to_download_file'), data=None)

        extracted_text = None
        converter = None

        try:
            converter = PDFToTextConverter(file_path=file_path)
            extracted_text = converter.extract_text()
            self.logger.info(f"Extracted {len(extracted_text.get('text', ''))} characters from PDF")
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return APIResponse(error_code=1, message=_('error_extracting_cv_content'), data=None)
        finally:
            if converter:
                converter.close()
            if os.path.exists(file_path):
                os.remove(file_path)

        if not extracted_text or not extracted_text.get('text'):
            return APIResponse(error_code=1, message=_('no_text_extracted'), data=None)

        try:
            cv_analyzer = CVAnalyzer()
            ai_result = await cv_analyzer.analyze_cv_content(
                extracted_text['text'], request.job_description
            )
            if ai_result is None:
                return APIResponse(error_code=1, message=_('error_analyzing_cv'), data=None)
            mapped_result = ai_to_cvbase(ai_result)
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return APIResponse(error_code=1, message=_('error_analyzing_cv'), data=None)

        return APIResponse(
            error_code=0,
            message=_('cv_processed_successfully'),
            data={
                'cv_file_url': request.cv_file_url,
                'extracted_text': extracted_text['text'],
                'cv_analysis_result': mapped_result.dict(),
                'jd_alignment': getattr(ai_result, "alignment_with_jd", None),
            },
        )

    async def _download_file(self, url: str) -> Optional[str]:
        temp_dir = tempfile.gettempdir()
        file_extension = 'pdf'
        file_name = f"cv_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(temp_dir, file_name)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(await response.read())
                        self.logger.info(f"Downloaded CV to {file_path}")
                        return file_path
                    else:
                        self.logger.error(f"Failed to download: HTTP {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            return None
