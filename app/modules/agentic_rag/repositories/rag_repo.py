"""
Repository for RAG operations using Langchain and Qdrant.
"""

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.modules.agentic_rag.schemas.rag_schema import (
	RAGRequest,
	RAGResponse,
	CitedSource,
)
from app.modules.agentic_rag.repositories.kb_repo import KBRepository
from app.modules.agentic_rag.schemas.kb_schema import QueryRequest
from app.core.config import GOOGLE_API_KEY


class RAGRepository:
	"""Repository for generating responses using RAG techniques."""

	def __init__(self) -> None:
		"""Initialize RAG repository."""
		# Create our own KBRepository instance
		self.kb_repo = KBRepository()

		# Initialize the LLM
		try:
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-1.5-pro',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
			print('RAGRepository: Initialized ChatGoogleGenerativeAI')
		except Exception as e:
			print(f'RAGRepository: Error initializing LLM: {e}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		# Define the default RAG prompt
		self.rag_prompt_template = PromptTemplate(
			input_variables=['context', 'question'],
			template="""You are a helpful and precise assistant. Use the following context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Always provide a detailed and comprehensive answer based only on the context provided.
            
            Context:
            {context}
            
            Question: {question}
            
            Helpful Answer:""",
		)

	async def generate(self, request: RAGRequest) -> RAGResponse:
		"""Generate a response using RAG based on the query."""
		try:
			# Retrieve documents from the knowledge base
			query_response = await self.kb_repo.query(QueryRequest(query=request.query, top_k=request.top_k))

			if not query_response.results:
				print(f"RAGRepository: No results found for query '{request.query}'")
				return RAGResponse(
					answer="I don't have enough information to answer this question based on the available knowledge.",
					sources=[],
					usage={
						'prompt_tokens': 0,
						'completion_tokens': 0,
						'total_tokens': 0,
					},
				)

			# Prepare the context by combining the contents of retrieved documents
			context = '\n\n'.join([f'Document {i + 1}:\n{doc.content}' for i, doc in enumerate(query_response.results)])

			# Create a RetrievelQA chain with the prepared context
			qa_chain = self.create_qa_chain(request.temperature)

			# Generate the response
			result = qa_chain.invoke({'context': context, 'question': request.query})

			# Create the sources information for each document
			sources = [
				CitedSource(
					id=doc.id,
					content=(doc.content[:200] + '...' if len(doc.content) > 200 else doc.content),
					score=doc.score,
					metadata=doc.metadata,
				)
				for doc in query_response.results
			]

			# Create token usage estimation (example values, replace with actual tracking)
			usage = {
				'prompt_tokens': len(context) // 4 + len(request.query) // 4,  # Approximation
				'completion_tokens': len(result['result']) // 4,  # Approximation
				'total_tokens': (len(context) + len(request.query) + len(result['result'])) // 4,  # Approximation
			}

			print(f"RAGRepository: Generated response for query '{request.query}'")
			return RAGResponse(answer=result['result'], sources=sources, usage=usage)

		except Exception as e:
			print(f'RAGRepository: Error generating response: {e}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

	def create_qa_chain(self, temperature: float) -> Any:
		"""Create a QA chain for answering questions with context."""
		try:
			# Create a new LLM instance with the requested temperature
			llm = ChatGoogleGenerativeAI(
				model='gemini-1.5-pro',
				google_api_key=GOOGLE_API_KEY,
				temperature=temperature,
				convert_system_message_to_human=True,
			)

			# Create chain directly with prompt and llm
			from langchain.chains import LLMChain

			chain = LLMChain(
				llm=llm,
				prompt=self.rag_prompt_template,
			)

			return chain
		except Exception as e:
			print(f'RAGRepository: Error creating QA chain: {e}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
