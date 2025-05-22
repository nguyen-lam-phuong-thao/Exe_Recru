"""
Pydantic models for Agentic RAG operations beyond basic knowledge base.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.core.base_model import RequestSchema


class RAGRequest(RequestSchema):
	"""Schema for performing a RAG query with optional context."""

	query: str = Field(..., description='User query to be answered using the knowledge base')
	top_k: int = Field(default=5, description='Number of documents to retrieve for context')
	temperature: float = Field(default=0.7, description='Temperature for generation')
	context_strategy: str = Field(
		default='merge',
		description="Strategy for using context: 'merge', 'chain', or 'rerank'",
	)


class CitedSource(BaseModel):
	"""Information about a source document used in the response."""

	id: str = Field(..., description='Source document ID')
	content: str = Field(..., description='Relevant content excerpt')
	score: float = Field(..., description='Relevance score')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Source metadata')


class RAGResponse(BaseModel):
	"""Schema for RAG response with sources."""

	answer: str = Field(..., description='Generated answer to the query')
	sources: List[CitedSource] = Field(..., description='Source documents used in the answer')
	usage: Dict[str, Any] = Field(default_factory=dict, description='Token usage information')
