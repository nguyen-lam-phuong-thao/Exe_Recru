"""Agentic RAG Knowledge Base routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.modules.agentic_rag.schemas.kb_schema import (
    AddDocumentsRequest,
    QueryRequest,
    UploadDocumentResponse,
    ViewDocumentResponse,
)
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

# Router for Agentic RAG knowledge base operations
route: APIRouter = APIRouter(prefix="/kb", tags=["Agentic RAG"])


def get_kb_repo():
    """Dependency to get KB repository instance."""
    return KBRepository()


@route.post("/documents", response_model=APIResponse)
async def add_documents(
    request: AddDocumentsRequest,
    kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
    """Add a list of documents to the Qdrant knowledge base."""
    try:
        ids: List[str] = await kb_repo.add_documents(request)
        print(f"[DEBUG] add_documents: Added document IDs: {ids}")
        return APIResponse(
            error_code=0, message=_("documents_added_successfully"), data={"ids": ids}
        )
    except CustomHTTPException as e:
        print(f"[DEBUG] add_documents error: {e.message}")
        return APIResponse(error_code=e.status_code, message=e.message, data=None)
    except Exception as e:
        print(f"[DEBUG] add_documents unexpected error: {e}")
        raise CustomHTTPException(message=_("error_occurred"))


@route.post("/query", response_model=APIResponse)
async def query_kb(
    request: QueryRequest,
    kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
    """Query the Qdrant knowledge base for similar documents."""
    try:
        result = await kb_repo.query(request)
        print(f"[DEBUG] query_kb: Retrieved results: {result}")
        return APIResponse(error_code=0, message=_("query_successful"), data=result)
    except CustomHTTPException as e:
        print(f"[DEBUG] query_kb error: {e.message}")
        return APIResponse(error_code=e.status_code, message=e.message, data=None)
    except Exception as e:
        print(f"[DEBUG] query_kb unexpected error: {e}")
        raise CustomHTTPException(message=_("error_occurred"))


@route.post("/upload", response_model=APIResponse)
async def upload_document(
    file: UploadFile = File(...),
    kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
    """Upload a file (PDF, TXT, MD) to the knowledge base."""
    try:
        print(
            f"[DEBUG] upload_document: Received file upload request for {file.filename}"
        )
        document_response: UploadDocumentResponse = await kb_repo.upload_file(file)
        print(
            f"[DEBUG] upload_document: File {file.filename} uploaded successfully with ID: {document_response.id}"
        )
        return APIResponse(
            error_code=0,
            message=_("file_uploaded_successfully"),
            data=document_response.model_dump(),
        )
    except CustomHTTPException as e:
        print(f"[DEBUG] upload_document error: {e.message}")
        return APIResponse(error_code=e.status_code, message=e.message, data=None)
    except Exception as e:
        print(f"[DEBUG] upload_document unexpected error: {e}")
        raise CustomHTTPException(message=_("error_occurred"))


@route.get("/documents/{document_id}", response_model=APIResponse)
async def get_document(
    document_id: str,
    kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
    """Retrieve a document from the knowledge base by its ID."""
    try:
        print(f"[DEBUG] get_document: Retrieving document with ID: {document_id}")
        document: Optional[ViewDocumentResponse] = await kb_repo.get_document(
            document_id
        )

        if document is None:
            print(f"[DEBUG] get_document: Document with ID {document_id} not found")
            raise NotFoundException(resource_name="document")

        print(
            f"[DEBUG] get_document: Document with ID {document_id} retrieved successfully"
        )
        return APIResponse(
            error_code=0,
            message=_("document_retrieved_successfully"),
            data=document.model_dump(),
        )
    except CustomHTTPException as e:
        print(f"[DEBUG] get_document error: {e.message}")
        return APIResponse(error_code=e.status_code, message=e.message, data=None)
    except Exception as e:
        print(f"[DEBUG] get_document unexpected error: {e}")
        raise CustomHTTPException(message=_("error_occurred"))


@route.delete("/documents/{document_id}", response_model=APIResponse)
async def delete_document(
    document_id: str,
    kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
    """Delete a document from the knowledge base by its ID."""
    try:
        print(f"[DEBUG] delete_document: Deleting document with ID: {document_id}")

        # Check if document exists first
        document = await kb_repo.get_document(document_id)
        if document is None:
            print(f"[DEBUG] delete_document: Document with ID {document_id} not found")
            raise NotFoundException(resource_name="document")

        # Delete the document
        success = await kb_repo.delete_document(document_id)

        if not success:
            print(
                f"[DEBUG] delete_document: Failed to delete document with ID {document_id}"
            )
            raise CustomHTTPException(message=_("error_deleting_document"))

        print(
            f"[DEBUG] delete_document: Document with ID {document_id} deleted successfully"
        )
        return APIResponse(
            error_code=0, message=_("document_deleted_successfully"), data=None
        )
    except CustomHTTPException as e:
        print(f"[DEBUG] delete_document error: {e.message}")
        return APIResponse(error_code=e.status_code, message=e.message, data=None)
    except Exception as e:
        print(f"[DEBUG] delete_document unexpected error: {e}")
        raise CustomHTTPException(message=_("error_occurred"))
