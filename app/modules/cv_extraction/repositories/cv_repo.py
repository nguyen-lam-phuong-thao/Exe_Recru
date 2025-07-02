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
from app.utils.pdf import (
	PDFToTextConverter,
)

class CVRepository:
	def __init__(self):
		self.logger = logging.getLogger(self.__class__.__name__)

	async def process_uploaded_cv(self, file: UploadFile, job_description: Optional[str] = None) -> APIResponse:
		self.logger.info(f"Processing uploaded file: {file.filename}")

		# Validate extension
		file_extension = file.filename.split('.')[-1].lower()
		if file_extension not in ['pdf', 'docx', 'txt']:
			self.logger.error(f'Unsupported file type: {file_extension}')
			return APIResponse(
				error_code=1,
				message=_('unsupported_cv_file_type'),
				data=None,
			)

		# Save uploaded file to temp
		try:
			with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp:
				temp_path = tmp.name
				self.logger.info(f'Saving uploaded file to: {temp_path}')
				shutil.copyfileobj(file.file, tmp)
		except Exception as e:
			self.logger.error(f'Failed to save uploaded file: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('failed_to_save_uploaded_file'),
				data=None,
			)

		self.logger.info(f'File saved. Beginning extraction...')

		extracted_text = None
		converter = None

		try:
			if file_extension == 'pdf':
				converter = PDFToTextConverter(file_path=temp_path)
				extracted_text = converter.extract_text()
				self.logger.info(f'Extracted {len(extracted_text)} characters from PDF')
			else:
				self.logger.error(f'No converter implemented for file type: {file_extension}')
				return APIResponse(
					error_code=1,
					message=_('unsupported_cv_file_type'),
					data=None,
				)
		except Exception as e:
			self.logger.error(f'Error during extraction: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_extracting_cv_content'),
				data=None,
			)
		finally:
			if isinstance(converter, PDFToTextConverter):
				converter.close()
			if os.path.exists(temp_path):
				os.remove(temp_path)
				self.logger.info(f'Temporary file deleted: {temp_path}')

		if not extracted_text:
			return APIResponse(
				error_code=1,
				message=_('no_text_extracted'),
				data=None,
			)

		self.logger.info('Analyzing extracted text with CVAnalyzer')
		try:
			cv_analyzer = CVAnalyzer()
			ai_result = await cv_analyzer.analyze_cv_content(extracted_text['text'], job_description)
			if ai_result is None:
				return APIResponse(
					error_code=1,
					message=_('error_analyzing_cv'),
					data=None,
				)
			mapped_result = ai_to_cvbase(ai_result)

		except Exception as e:
			self.logger.error(f'Analysis failed: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)

		return APIResponse(
			error_code=0,
			message=_('cv_processed_successfully'),
			data={
				'filename': file.filename,
				'extracted_text': extracted_text['text'],
				'cv_analysis_result': mapped_result.dict(),
				'jd_alignment': ai_result.alignment_with_jd,
			},
		)

	async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
		self.logger.info(f'Starting process_cv method with request: {request}')
		# DOWNLOAD CV FROM URL
		self.logger.info(f'Attempting to download CV from URL: {request.cv_file_url}')
		file_path = await self._download_file(request.cv_file_url)
		if not file_path:
			self.logger.error('Download failed, returning error response')
			return APIResponse(
				error_code=1,
				message=_('failed_to_download_file'),
				data=None,
			)

		self.logger.info(f'File downloaded successfully to: {file_path}')
		extracted_text = None
		file_extension = 'pdf'
		self.logger.info(f'Detected file extension: {file_extension}')
		converter = None

		try:
			if file_extension == 'pdf':
				self.logger.info('Processing PDF file')
				converter = PDFToTextConverter(file_path=file_path)
				self.logger.info('Initialized PDFToTextConverter')
				extracted_text = converter.extract_text()
				self.logger.info(f'PDF text extraction complete, extracted {len(extracted_text)} characters')
			else:
				self.logger.error(f'Unsupported file type detected: {file_extension}')
				if os.path.exists(file_path):
					self.logger.info(f'Removing unsupported file: {file_path}')
					os.remove(file_path)
				return APIResponse(
					error_code=1,
					message=_('unsupported_cv_file_type'),
					data=None,
				)

		except Exception as e:
			self.logger.error(f'Exception during text extraction: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_extracting_cv_content'),
				data=None,
			)
		finally:
			self.logger.info('Entering finally block for cleanup')
			if isinstance(converter, PDFToTextConverter):
				self.logger.info('Closing PDF converter')
				converter.close()
			if os.path.exists(file_path):
				self.logger.info(f'Removing temporary file: {file_path}')
				os.remove(file_path)

		self.logger.info('Process completed successfully')
		self.logger.info(f'Extracted text length: {len(extracted_text) if extracted_text else 0}')
		if not extracted_text:
			self.logger.error('No text extracted, returning error response')
			return APIResponse(
				error_code=1,
				message=_('no_text_extracted'),
				data=None,
			)

		cv_analyzer = CVAnalyzer()
		self.logger.info('Initialized CVAnalyzer')
		try:
			self.logger.info('Starting CV analysis')
			self.logger.info(f'Extracted text: {extracted_text}')
			ai_result = await cv_analyzer.analyze_cv_content(extracted_text['text'])
			self.logger.info(f'CV analysis result: {ai_result}')
			if ai_result is None:
				return APIResponse(
					error_code=1,
					message=_('error_analyzing_cv'),
					data=None,
				)
			mapped_result = ai_to_cvbase(ai_result)
		except Exception as e:
			self.logger.error(f'Exception during CV analysis: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)
		return APIResponse(
			error_code=0,
			message=_('cv_processed_successfully'),
			data={
				'cv_file_url': request.cv_file_url,
				'extracted_text': extracted_text['text'],
				'cv_analysis_result': mapped_result.dict(),
			},
		)

	async def _download_file(self, url: str) -> str | None:
		temp_dir = 'temp_cvs'
		if not os.path.exists(temp_dir):
			os.makedirs(temp_dir)
			self.logger.info(f'Created temporary directory: {temp_dir}')

		# Extract file extension from the URL
		file_extension = 'pdf'
		if file_extension not in ['pdf', 'docx', 'txt']:
			self.logger.error(f'Invalid file type: {file_extension} for URL: {url}')
			return None

		file_name = f'cv_{uuid.uuid4()}.{file_extension}'
		file_path = os.path.join(temp_dir, file_name)
		self.logger.info(f'Attempting to download file from {url} to {file_path}')

		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(url, ssl=False) as response:
					self.logger.info(f'Response: {response}')
					if response.status == 200:
						self.logger.info(f'Download successful (Status: {response.status})')
						async with aiofiles.open(file_path, 'wb') as f:
							await f.write(await response.read())
						self.logger.info(f'File saved to {file_path}')
						return file_path
					else:
						self.logger.error(f'Failed to download file from {url}, status: {response.status}')
						return None

		except Exception as e:
			self.logger.error(f'Error downloading file from {url}: {e}')
			return None
			async with aiohttp.ClientSession() as session:
				async with session.get(url, ssl=False) as response:
					self.logger.info(f'Response: {response}')
					if response.status == 200:
						self.logger.info(f'Download successful (Status: {response.status})')
						async with aiofiles.open(file_path, 'wb') as f:
							await f.write(await response.read())
						self.logger.info(f'File saved to {file_path}')
						return file_path
					else:
						self.logger.error(f'Failed to download file from {url}, status: {response.status}')
						return None

		except Exception as e:
			self.logger.error(f'Error downloading file from {url}: {e}')
			return None
