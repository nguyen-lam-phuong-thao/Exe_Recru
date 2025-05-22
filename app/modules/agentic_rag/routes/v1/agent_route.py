"""Agentic RAG Agent routes."""

from fastapi import APIRouter, Depends

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.modules.agentic_rag.schemas.rag_schema import RAGRequest
from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

# Router for Agentic RAG agent operations
route: APIRouter = APIRouter(prefix='/agent', tags=['Agentic RAG'])


def get_kb_repo():
	"""Dependency to get KB repository instance."""
	return KBRepository()


@route.post('/answer', response_model=APIResponse)
async def answer_query(
	request: RAGRequest,
	kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
	"""Generate a response using a LangGraph-based agent with knowledge base."""
	try:
		# Initialize the agent with our KB repository
		agent = RAGAgentGraph(kb_repo=kb_repo)

		# Process the query
		result = await agent.answer_query(request.query)

		print(f'[DEBUG] answer_query: Generated response with {len(result.get("sources", []))} sources')
		return APIResponse(error_code=0, message=_('response_generated_successfully'), data=result)
	except CustomHTTPException as e:
		print(f'[DEBUG] answer_query error: {e.message}')
		return APIResponse(error_code=e.status_code, message=e.message, data=None)
	except Exception as e:
		print(f'[DEBUG] answer_query unexpected error: {e}')
		raise CustomHTTPException(status_code=500, message=_('error_occurred'))
