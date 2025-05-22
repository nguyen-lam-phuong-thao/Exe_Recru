import time
from typing import List

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.modules.agentic_rag.schemas.kb_schema import (
    AddDocumentsRequest,
    QueryRequest,
    QueryResponse,
    QueryResponseItem,
)
from app.core.config import GOOGLE_API_KEY
from app.modules.agentic_rag.core.config import settings


class KBRepository:
    """Repository for interacting with the Qdrant knowledge base."""

    def __init__(self) -> None:
        # Initialize Qdrant client and vector store
        qdrant_url: str = settings.QdrantUrl
        qdrant_api_key: str = settings.QdrantApiKey
        self.collection_name: str = settings.QdrantCollection

        # Print connection details for debugging
        print(f"KBRepository: Connecting to Qdrant at {qdrant_url}")

        # Add retry logic for Docker networking issues
        max_retries = 5
        retry_delay = 3  # seconds

        for attempt in range(max_retries):
            try:
                # Initialize Qdrant client
                self.client: QdrantClient = QdrantClient(
                    url=qdrant_url, api_key=qdrant_api_key if qdrant_api_key else None
                )
                print("KBRepository: Initialized Qdrant client successfully")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(
                        f"KBRepository: Error initializing Qdrant client (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    print(f"KBRepository: Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(
                        f"KBRepository: Error initializing Qdrant client after {max_retries} attempts: {e}"
                    )
                    raise CustomHTTPException(
                        status_code=500, message=_("error_initializing_qdrant_client")
                    )

        # Initialize embeddings using Google's GenerativeAI embeddings
        try:
            self.embedding = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001", google_api_key=GOOGLE_API_KEY
            )
            print("KBRepository: Initialized Google GenerativeAI embeddings")
        except Exception as e:
            print(f"KBRepository: Error initializing embeddings: {e}")
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))

        try:
            # Create or load existing Qdrant collection via LangChain wrapper
            # Add retry logic for collection creation/connection
            for attempt in range(max_retries):
                try:
                    self.vectorstore = QdrantVectorStore(
                        client=self.client,
                        collection_name=self.collection_name,
                        embedding=self.embedding,  # Corrected: embedding to embeddings
                        metadata_payload_key="metadata",  # Using the default metadata key
                    )
                    print(
                        f"KBRepository: Connected to Qdrant collection '{self.collection_name}' at {qdrant_url}"
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(
                            f"KBRepository: Error connecting to collection (attempt {attempt + 1}/{max_retries}): {e}"
                        )
                        print(f"KBRepository: Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        raise  # Re-raise to be caught by outer try-except
        except Exception as e:
            print(f"KBRepository: Error initializing Qdrant vector store: {e}")
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))

    async def add_documents(self, request: AddDocumentsRequest) -> List[str]:
        """Add documents to the knowledge base."""
        try:
            docs: List[Document] = []
            for doc in request.documents:
                docs.append(
                    Document(
                        page_content=doc.content,
                        metadata=doc.metadata,
                        id=doc.id,
                    )
                )
            self.vectorstore.add_documents(documents=docs)
            ids: List[str] = [doc.id for doc in request.documents]
            print(f"KBRepository: Added documents with IDs: {ids}")
            return ids
        except Exception as e:
            print(f"KBRepository: Error adding documents: {e}")
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query the knowledge base for similar documents."""
        try:
            results = self.vectorstore.similarity_search(
                query=request.query,
                k=request.top_k,
            )
            items: List[QueryResponseItem] = []
            for res in results:
                item = QueryResponseItem(
                    id=res.id,  # type: ignore
                    content=res.page_content,
                    score=getattr(res, "score", 0.0),  # type: ignore
                    metadata=res.metadata or {},
                )
                items.append(item)
            print(
                f"KBRepository: Retrieved {len(items)} results for query '{request.query}'"
            )
            return QueryResponse(results=items)
        except Exception as e:
            print(f"KBRepository: Error querying knowledge base: {e}")
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))
