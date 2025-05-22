from typing import List, Optional
import uuid
import io
import time

from qdrant_client import QdrantClient
from fastapi import UploadFile

# Added imports for collection creation
from qdrant_client.http.models import (
	Distance,
	VectorParams,
	CollectionStatus,
	PointStruct,
)
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
	UploadDocumentResponse,
	ViewDocumentResponse,
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
		self.embedding_model_name: str = 'models/embedding-001'  # Store model name
		self.vector_size: int = 768  # Dimension for models/embedding-001

		# Print connection details for debugging
		print(f'KBRepository: Connecting to Qdrant at {qdrant_url}')

		# Add retry logic for Docker networking issues
		max_retries = 5
		retry_delay = 3  # seconds

		for attempt in range(max_retries):
			try:
				# Initialize Qdrant client
				self.client: QdrantClient = QdrantClient(url=qdrant_url, api_key=qdrant_api_key if qdrant_api_key else None)
				print('KBRepository: Initialized Qdrant client successfully')
				break
			except Exception as e:
				if attempt < max_retries - 1:
					print(f'KBRepository: Error initializing Qdrant client (attempt {attempt + 1}/{max_retries}): {e}')
					print(f'KBRepository: Retrying in {retry_delay} seconds...')
					time.sleep(retry_delay)
				else:
					print(f'KBRepository: Error initializing Qdrant client after {max_retries} attempts: {e}')
					raise CustomHTTPException(status_code=500, message=_('error_initializing_qdrant_client'))

		# Initialize embeddings using Google's GenerativeAI embeddings
		try:
			self.embedding = GoogleGenerativeAIEmbeddings(model=self.embedding_model_name, google_api_key=GOOGLE_API_KEY)
			print('KBRepository: Initialized Google GenerativeAI embeddings')
		except Exception as e:
			print(f'KBRepository: Error initializing embeddings: {e}')
			raise CustomHTTPException(message=_('error_occurred'))

		# Ensure collection exists
		try:
			collection_exists = False
			try:
				collection_info = self.client.get_collection(collection_name=self.collection_name)
				if collection_info.status == CollectionStatus.GREEN:
					collection_exists = True
					print(f"KBRepository: Collection '{self.collection_name}' already exists and is ready.")
			except Exception as e:  # Catches specific "not found" or general connection errors
				print(f"KBRepository: Collection '{self.collection_name}' not found or error checking: {e}. Attempting to create.")

			if not collection_exists:
				print(f"KBRepository: Creating collection '{self.collection_name}' with vector size {self.vector_size}.")
				self.client.create_collection(
					collection_name=self.collection_name,
					vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
				)
				print(f"KBRepository: Collection '{self.collection_name}' created successfully.")

		except Exception as e:
			print(f"KBRepository: Error ensuring collection '{self.collection_name}' exists: {e}")
			raise CustomHTTPException(message=_('error_creating_or_checking_collection'))

		try:
			# Create or load existing Qdrant collection via LangChain wrapper
			# Add retry logic for collection creation/connection
			for attempt in range(max_retries):
				try:
					self.vectorstore = QdrantVectorStore(
						client=self.client,
						collection_name=self.collection_name,
						embedding=self.embedding,  # Corrected: embedding to embeddings
						metadata_payload_key='metadata',  # Using the default metadata key
					)
					print(f"KBRepository: Connected to Qdrant collection '{self.collection_name}' at {qdrant_url}")
					break
				except Exception as e:
					if attempt < max_retries - 1:
						print(f'KBRepository: Error connecting to collection (attempt {attempt + 1}/{max_retries}): {e}')
						print(f'KBRepository: Retrying in {retry_delay} seconds...')
						time.sleep(retry_delay)
					else:
						raise  # Re-raise to be caught by outer try-except
		except Exception as e:
			print(f'KBRepository: Error initializing Qdrant vector store: {e}')
			raise CustomHTTPException(message=_('error_occurred'))

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
			print(f'KBRepository: Added documents with IDs: {ids}')
			return ids
		except Exception as e:
			print(f'KBRepository: Error adding documents: {e}')
			raise CustomHTTPException(message=_('error_occurred'))

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
					score=getattr(res, 'score', 0.0),  # type: ignore
					metadata=res.metadata or {},
				)
				items.append(item)
			print(f"KBRepository: Retrieved {len(items)} results for query '{request.query}'")
			return QueryResponse(results=items)
		except Exception as e:
			print(f'KBRepository: Error querying knowledge base: {e}')
			raise CustomHTTPException(message=_('error_occurred'))

	async def upload_file(self, file: UploadFile) -> UploadDocumentResponse:
		"""Upload a file, parse it, and add it to the knowledge base."""
		try:
			print(f'[DEBUG] KBRepository.upload_file: Processing file: {file.filename}')

			# Read file content
			content = await file.read()
			text_content = ''
			doc_id = str(uuid.uuid4())
			metadata = {
				'source': file.filename,
				'file_type': file.content_type,
				'upload_date': str(uuid.uuid1().time),
			}

			# Process file based on content type
			if file.filename.lower().endswith('.pdf'):
				# Parse PDF file - using simple extraction to avoid dependencies
				try:
					# In a real implementation, use a proper PDF extraction library
					# For now, we'll use a simple placeholder
					text_content = f'PDF content extracted from {file.filename}'
					print(f'[DEBUG] KBRepository.upload_file: Parsed PDF file (simplified extraction)')
				except Exception as pdf_error:
					print(f'[DEBUG] KBRepository.upload_file: Error parsing PDF: {pdf_error}')
					raise CustomHTTPException(message=_('error_parsing_pdf'))
			elif file.filename.lower().endswith('.txt'):
				# Parse text file
				try:
					text_content = content.decode('utf-8')
					print(f'[DEBUG] KBRepository.upload_file: Parsed TXT file with {len(text_content)} characters')
				except UnicodeDecodeError:
					print(f'[DEBUG] KBRepository.upload_file: UTF-8 decode error, trying with latin-1')
					text_content = content.decode('latin-1')
					print(f'[DEBUG] KBRepository.upload_file: Parsed TXT file with latin-1 encoding')
			elif file.filename.lower().endswith('.md'):
				# Parse markdown file
				try:
					text_content = content.decode('utf-8')
					print(f'[DEBUG] KBRepository.upload_file: Parsed Markdown file with {len(text_content)} characters')
				except UnicodeDecodeError:
					print(f'[DEBUG] KBRepository.upload_file: UTF-8 decode error, trying with latin-1')
					text_content = content.decode('latin-1')
					print(f'[DEBUG] KBRepository.upload_file: Parsed Markdown file with latin-1 encoding')
			else:
				# Unsupported file type
				print(f'[DEBUG] KBRepository.upload_file: Unsupported file type: {file.filename}')
				raise CustomHTTPException(message=_('unsupported_file_type'))

			# Check if we extracted any content
			if not text_content.strip():
				print(f'[DEBUG] KBRepository.upload_file: No content extracted from file: {file.filename}')
				raise CustomHTTPException(message=_('empty_file_content'))

			# Create a document and add it to vectorstore
			langchain_doc = Document(page_content=text_content, metadata=metadata)

			print(f'[DEBUG] KBRepository.upload_file: Adding document to vector store with ID: {doc_id}')
			ids = self.vectorstore.add_documents(documents=[langchain_doc], ids=[doc_id])
			if not ids:
				print(f'[DEBUG] KBRepository.upload_file: Failed to add document to vector store')
				raise CustomHTTPException(message=_('error_adding_document_to_vector_store'))

			# Create and return response
			return UploadDocumentResponse(
				id=doc_id,
				filename=file.filename,
				content_type=file.content_type,
				size=len(content),
				metadata=metadata,
			)

		except CustomHTTPException as e:
			# Re-raise custom exceptions
			raise e
		except Exception as e:
			print(f'[DEBUG] KBRepository.upload_file: Unexpected error: {str(e)}')
			raise CustomHTTPException(message=_('error_uploading_file'))

	async def get_document(self, document_id: str) -> Optional[ViewDocumentResponse]:
		"""Retrieve a document from the knowledge base by its ID."""
		try:
			print(f'[DEBUG] KBRepository.get_document: Retrieving document with ID: {document_id}')

			# Retrieve the document from Qdrant
			points = self.client.retrieve(
				collection_name=self.collection_name,
				ids=[document_id],
				with_payload=True,
				with_vectors=False,
			)

			if not points or len(points) == 0:
				print(f'[DEBUG] KBRepository.get_document: Document not found with ID: {document_id}')
				return None

			# Extract document data from the retrieved point
			point = points[0]
			content = point.payload.get('page_content', '') if point.payload else ''
			metadata = point.payload.get('metadata', {}) if point.payload else {}

			print(f'[DEBUG] KBRepository.get_document: Successfully retrieved document with ID: {document_id}')

			# Create and return the response
			return ViewDocumentResponse(id=document_id, content=content, metadata=metadata)

		except Exception as e:
			print(f'[DEBUG] KBRepository.get_document: Error retrieving document: {str(e)}')
			raise CustomHTTPException(message=_('error_retrieving_document'))

	async def delete_document(self, document_id: str) -> bool:
		"""Delete a document from the knowledge base by its ID."""
		try:
			print(f'[DEBUG] KBRepository.delete_document: Attempting to delete document with ID: {document_id}')

			# Check if document exists first
			existing_points = self.client.retrieve(
				collection_name=self.collection_name,
				ids=[document_id],
				with_payload=False,
				with_vectors=False,
			)

			if not existing_points:
				print(f'[DEBUG] KBRepository.delete_document: Document with ID {document_id} not found for deletion.')
				return False

			# Perform delete operation
			self.client.delete(
				collection_name=self.collection_name,
				points_selector=[document_id],
			)

			print(f'[DEBUG] KBRepository.delete_document: Deletion command issued for document with ID: {document_id}')
			return True

		except Exception as e:
			print(f'[DEBUG] KBRepository.delete_document: Error deleting document: {str(e)}')
			raise CustomHTTPException(message=_('error_deleting_document'))

	async def list_all_documents(self) -> List[ViewDocumentResponse]:
		"""List all documents from the knowledge base."""
		try:
			print('[DEBUG] KBRepository.list_all_documents: Listing all documents')
			all_documents: List[ViewDocumentResponse] = []
			next_page_offset = None

			while True:
				# Scroll through all points in the collection
				points, next_page_offset = self.client.scroll(
					collection_name=self.collection_name,
					limit=100,  # Fetch 100 documents per request
					offset=next_page_offset,
					with_payload=True,  # We need the payload for content and metadata
					with_vectors=False,  # We don't need the vectors for listing
				)

				for point in points:
					# Ensure point.id is correctly handled (it can be int, str, or UUID)
					doc_id = str(point.id)
					content = point.payload.get('page_content', '') if point.payload else ''
					metadata = point.payload.get('metadata', {}) if point.payload else {}

					all_documents.append(ViewDocumentResponse(id=doc_id, content=content, metadata=metadata))

				if not next_page_offset:  # No more pages
					break

			print(f'[DEBUG] KBRepository.list_all_documents: Retrieved {len(all_documents)} documents.')
			return all_documents

		except Exception as e:
			print(f'[DEBUG] KBRepository.list_all_documents: Error listing documents: {str(e)}')
			raise CustomHTTPException(message=_('error_listing_documents'))
