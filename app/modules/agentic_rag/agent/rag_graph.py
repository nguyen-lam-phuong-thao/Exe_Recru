"""
LangGraph implementation for Agentic RAG workflows.
"""

import uuid
from typing import Dict, List, Any, TypedDict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.core.config import GOOGLE_API_KEY
from app.modules.agentic_rag.repositories.kb_repo import KBRepository


class AgentState(TypedDict):
	"""State for the Agentic RAG workflow."""

	query: str
	retrieved_documents: List[Document]
	answer: Optional[str]
	sources: List[Dict[str, Any]]
	messages: List[Any]
	error: Optional[str]


class RAGAgentGraph:
	"""LangGraph-based agent for RAG operations."""

	def __init__(self, kb_repo: Optional[KBRepository] = None) -> None:
		"""Initialize the RAG agent graph."""
		self.kb_repo = kb_repo or KBRepository()

		try:
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-1.5-pro',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
			print('RAGAgentGraph: Initialized ChatGoogleGenerativeAI')
		except Exception as e:
			print(f'RAGAgentGraph: Error initializing LLM: {e}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		self.memory = MemorySaver()  # In-memory checkpointer for state
		self.workflow = self._build_graph()

	async def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
		"""Retrieve relevant documents based on the query."""
		print('RetrievalNode: Starting document retrieval')

		# Get the user query
		query = state.get('query', '')
		if not query:
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}

		try:
			# Retrieve documents using the KB repository
			from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

			# Use simpler approach for LangGraph integration
			query_response = await self.kb_repo.query(QueryRequest(query=query, top_k=5))

			# Convert to Document objects
			retrieved_docs = []
			for item in query_response.results:
				doc = Document(
					page_content=item.content,
					metadata=item.metadata,
				)
				doc.id = item.id  # type: ignore
				doc.score = item.score  # type: ignore
				retrieved_docs.append(doc)

			print(f'RetrievalNode: Retrieved {len(retrieved_docs)} documents')
			return {
				'retrieved_documents': retrieved_docs,
				'messages': state.get('messages', []) + [AIMessage(content=f'Retrieved {len(retrieved_docs)} documents')],
			}
		except Exception as e:
			print(f'RetrievalNode: Error retrieving documents: {e}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error retrieving documents: {e}')],
			}

	async def _generation_node(self, state: AgentState) -> Dict[str, Any]:
		"""Generate an answer based on retrieved documents."""
		print('GenerationNode: Starting answer generation')

		# Check if we have an error or documents
		if state.get('error'):
			return state

		docs = state.get('retrieved_documents', [])
		if not docs:
			return {
				'answer': "I don't have enough information to answer this question based on the available knowledge.",
				'sources': [],
				'messages': state.get('messages', []) + [AIMessage(content='No relevant information found for this query.')],
			}

		# Prepare context from retrieved documents
		context = '\n\n'.join([f'Document {i + 1} (ID: {doc.id}):\n{doc.page_content}' for i, doc in enumerate(docs)])

		# Define the generation prompt
		template = """You are a helpful and precise assistant. Use the following context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Always provide a detailed and comprehensive answer based only on the context provided.
        Include citations in your answer when you use information from specific documents.
        
        Context:
        {context}
        
        Question: {question}
        
        Helpful Answer:"""

		prompt = PromptTemplate(input_variables=['context', 'question'], template=template)

		try:
			# Prepare the prompt inputs
			prompt_inputs = {'context': context, 'question': state.get('query', '')}

			# Invoke the LLM
			from langchain.chains import LLMChain

			chain = LLMChain(llm=self.llm, prompt=prompt)
			result = chain.invoke(prompt_inputs)

			# Extract the answer
			answer = result.get('text', '')

			# Prepare source information for each document
			sources = []
			for doc in docs:
				sources.append({
					'id': getattr(doc, 'id', 'unknown'),
					'content': (doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content),
					'score': getattr(doc, 'score', 0.0),
					'metadata': doc.metadata or {},
				})

			print(f'GenerationNode: Generated answer with {len(sources)} sources')
			return {
				'answer': answer,
				'sources': sources,
				'messages': state.get('messages', []) + [AIMessage(content=answer)],
			}
		except Exception as e:
			print(f'GenerationNode: Error generating answer: {e}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error generating answer: {e}')],
			}

	def _should_end(self, state: AgentState) -> bool:
		"""Determine if the workflow should end."""
		# End if we have an answer or an error
		return bool(state.get('answer')) or bool(state.get('error'))

	def _build_graph(self) -> StateGraph:
		"""Construct the LangGraph StateGraph for the RAG workflow."""
		# Define the graph
		graph = StateGraph(AgentState)

		# Add nodes
		graph.add_node('retrieval', self._retrieval_node)
		graph.add_node('generation', self._generation_node)

		# Define the edges
		graph.add_edge('retrieval', 'generation')
		graph.add_conditional_edges(
			'generation',
			self._should_end,
			{
				True: END,
				False: 'retrieval',  # We could loop back for refinement, but for now we'll end
			},
		)

		# Set the entry point
		graph.set_entry_point('retrieval')

		# Compile the graph
		return graph.compile()

	async def answer_query(self, query: str) -> Dict[str, Any]:
		"""Process a query and return the answer with sources."""
		try:
			# Initialize the state
			state = {
				'query': query,
				'retrieved_documents': [],
				'answer': None,
				'sources': [],
				'messages': [
					SystemMessage(content='RAG Agent'),
					HumanMessage(content=query),
				],
				'error': None,
			}

			# Create a new session for this execution
			session_id = str(uuid.uuid4())

			# Execute the workflow
			result = await self.workflow.ainvoke(state, config={'configurable': {'session_id': session_id}})

			# Check if we got an error
			if result.get('error'):
				raise Exception(result['error'])

			# Return the results
			return {
				'answer': result.get('answer', ''),
				'sources': result.get('sources', []),
				'conversation': [msg.content for msg in result.get('messages', [])],
			}
		except Exception as e:
			print(f'RAGAgentGraph.answer_query: Error: {e}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
