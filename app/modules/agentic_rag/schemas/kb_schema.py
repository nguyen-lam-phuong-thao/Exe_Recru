# -*- coding: utf-8 -*-
"""
Pydantic models for Agentic RAG knowledge base operations.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.core.base_model import RequestSchema


class DocumentModel(BaseModel):
	"""Model representing a document to be added to the knowledge base."""

	id: str = Field(..., description='Unique identifier for the document')
	content: str = Field(..., description='Content of the document')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata for the document')


class AddDocumentsRequest(RequestSchema):
	"""Schema for adding documents to the knowledge base."""

	documents: List[DocumentModel] = Field(..., description='List of documents to add to the knowledge base')


class QueryRequest(RequestSchema):
	"""Schema for querying the knowledge base."""

	query: str = Field(..., description='Query text to search in the knowledge base')
	top_k: int = Field(default=5, description='Number of top similar documents to retrieve')


class QueryResponseItem(BaseModel):
	"""Item representing a single query result."""

	id: str = Field(..., description='Identifier of the matched document')
	content: str = Field(..., description='Content of the matched document')
	score: float = Field(..., description='Similarity score of the match')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Metadata of the matched document')


class QueryResponse(BaseModel):
	"""Schema for query response containing multiple results."""

	results: List[QueryResponseItem] = Field(..., description='List of query response items')
