"""Agentic RAG Knowledge Base routes."""

from typing import List

from fastapi import APIRouter, Depends

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.modules.agentic_rag.schemas.kb_schema import AddDocumentsRequest, QueryRequest
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

# Router for Agentic RAG knowledge base operations
route: APIRouter = APIRouter(prefix='/kb', tags=['Agentic RAG'])


def get_kb_repo():
	"""Dependency to get KB repository instance."""
	return KBRepository()


@route.post('/documents', response_model=APIResponse)
async def add_documents(
	request: AddDocumentsRequest,
	kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
	"""Add a list of documents to the Qdrant knowledge base."""
	try:
		ids: List[str] = await kb_repo.add_documents(request)
		print(f'[DEBUG] add_documents: Added document IDs: {ids}')
		return APIResponse(error_code=0, message=_('documents_added_successfully'), data={'ids': ids})
	except CustomHTTPException as e:
		print(f'[DEBUG] add_documents error: {e.message}')
		return APIResponse(error_code=e.status_code, message=e.message, data=None)
	except Exception as e:
		print(f'[DEBUG] add_documents unexpected error: {e}')
		raise CustomHTTPException(status_code=500, message=_('error_occurred'))


@route.post('/query', response_model=APIResponse)
async def query_kb(
	request: QueryRequest,
	kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
	"""Query the Qdrant knowledge base for similar documents."""
	try:
		result = await kb_repo.query(request)
		print(f'[DEBUG] query_kb: Retrieved results: {result}')
		return APIResponse(error_code=0, message=_('query_successful'), data=result)
	except CustomHTTPException as e:
		print(f'[DEBUG] query_kb error: {e.message}')
		return APIResponse(error_code=e.status_code, message=e.message, data=None)
	except Exception as e:
		print(f'[DEBUG] query_kb unexpected error: {e}')
		raise CustomHTTPException(status_code=500, message=_('error_occurred'))
