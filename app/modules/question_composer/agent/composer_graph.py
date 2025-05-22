import uuid
import re  # Import re for parsing LLM list outputs
from typing import Dict, List, Any, TypedDict, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # For LLM calls
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import GOOGLE_API_KEY  # For LLM
from app.middleware.translation_manager import _
from app.exceptions.exception import (
	CustomHTTPException,
)
from app.modules.question_composer.schemas.question_agent_schema import (
	GeneratedQuestion,  # Using this for structured question output
	UserCharacteristics,  # Corrected from UserCharacteristicsInput
)
from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph  # For KB queries
from app.modules.question_composer.prompts import prompt  # Import prompts


# --- State Definition ---
class QuestionComposerState(TypedDict):
	"""State for the Question Composer workflow."""

	user_characteristics: UserCharacteristics  # Corrected type
	knowledge_query: Optional[str]  # Query to be sent to RAG
	knowledge_context: Optional[Dict[str, Any]]  # Response from RAG
	initial_questions: List[GeneratedQuestion]
	critique: Optional[str]  # To store critique from self-reflection
	refined_questions: List[GeneratedQuestion]
	final_questions: List[GeneratedQuestion]
	current_iteration: int
	max_iterations: int  # For self-reflection loop
	num_questions_to_generate: int  # Number of questions to aim for at each generation step
	num_final_questions: int  # Number of questions to output
	messages: List[Any]  # For logging/tracing agent thoughts
	error: Optional[str]


# --- Node Implementations ---
class QuestionComposerGraph:
	"""LangGraph-based workflow for question composition."""

	def __init__(self, user_id: Optional[str] = None, session_id: Optional[str] = None, lang: str = 'en'):
		"""Initialize the Question Composer graph."""
		self.rag_agent_graph = RAGAgentGraph()
		self.memory = MemorySaver()
		self.lang = lang

		try:
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
			print('QuestionComposerGraph: Initialized ChatGoogleGenerativeAI')
		except Exception as e:
			print(f'QuestionComposerGraph: Error initializing LLM: {e}')
			raise CustomHTTPException(status_code=500, detail=_('error_llm_initialization', self.lang))

		self.workflow = self._build_graph()
		print('QuestionComposerGraph: Initialized.')

	def _parse_llm_generated_questions(self, llm_output: str, category: str = 'generated') -> List[GeneratedQuestion]:
		"""Parses a string of numbered questions from LLM into a list of GeneratedQuestion objects."""
		questions = []
		matches = re.findall(r'^\s*\d+\.\s*(.+)$', llm_output, re.MULTILINE)
		if not matches:
			if llm_output.strip():
				questions.append(GeneratedQuestion(id=f'{category}_{uuid.uuid4()}', text=llm_output.strip(), category=category))
		else:
			for i, q_text in enumerate(matches):
				questions.append(GeneratedQuestion(id=f'{category}_{uuid.uuid4()}', text=q_text.strip(), category=category))
		return questions

	async def _prepare_knowledge_query_node(self, state: QuestionComposerState) -> Dict[str, Any]:
		"""Prepares the query for the RAG system based on user characteristics using an LLM."""
		print('Node: _prepare_knowledge_query_node')
		user_chars_data = state.get('user_characteristics')
		if not user_chars_data or not user_chars_data.characteristics:
			print('Error: No user characteristics provided.')
			return {'error': _('error_missing_user_characteristics', self.lang)}

		try:
			prompt_str = prompt.PREPARE_KNOWLEDGE_QUERY_PROMPT.format(user_characteristics=str(user_chars_data.characteristics))
			llm_response = await self.llm.ainvoke([HumanMessage(content=prompt_str)])
			derived_query = llm_response.content.strip()

			print(f'LLM-derived knowledge query: {derived_query}')
			return {
				'knowledge_query': derived_query,
				'messages': state.get('messages', [])
				+ [AIMessage(content=get_translation(self.lang, 'info_preparing_knowledge_query')), AIMessage(content=f'Prepared knowledge query: {derived_query}')],
			}
		except Exception as e:
			print(f'Error in _prepare_knowledge_query_node: {e}')
			return {'error': _('error_knowledge_query_failed', self.lang), 'messages': state.get('messages', []) + [AIMessage(content=f'Error preparing knowledge query: {str(e)}')]}

	async def _query_knowledge_base_node(self, state: QuestionComposerState) -> Dict[str, Any]:
		"""Queries the RAG system (Knowledge Base) for relevant context."""
		print('Node: _query_knowledge_base_node')
		query = state.get('knowledge_query')
		messages = state.get('messages', [])
		messages.append(AIMessage(content=get_translation(self.lang, 'info_querying_knowledge_base')))

		if not query:
			print('Error: No knowledge query prepared.')
			return {
				'knowledge_context': {'knowledge': 'No query was provided to the knowledge base.', 'sources': []},
				'messages': messages + [AIMessage(content='Skipped knowledge base query as no query was prepared.')],
			}

		try:
			print(f'Querying RAG system with: {query}')
			rag_response: Dict[str, Any] = await self.rag_agent_graph.answer_query(query=query)
			print(f'RAG Response: {rag_response}')

			knowledge: str = rag_response.get('answer', 'No specific knowledge found.')
			if not knowledge and rag_response.get('error'):
				knowledge = f'Error from RAG: {rag_response.get("error")}'
			elif not knowledge and not rag_response.get('sources'):
				knowledge = 'No information found for the query.'

			knowledge_context = {'knowledge': knowledge, 'sources': rag_response.get('sources', [])}
			print(f'Retrieved knowledge context: {knowledge_context}')
			return {
				'knowledge_context': knowledge_context,
				'messages': messages + [AIMessage(content=f'Retrieved knowledge: {knowledge[:100]}... ({len(knowledge_context.get("sources", []))} sources)')],
			}
		except Exception as e:
			print(f'Error querying RAG system: {e}')
			error_message = _('error_knowledge_base_query_failed', self.lang) + f': {str(e)}'
			return {
				'knowledge_context': {'knowledge': error_message, 'sources': []},
				'error': error_message,
				'messages': messages + [AIMessage(content=f'Error querying knowledge base: {error_message}')],
			}

	async def _generate_initial_questions_node(self, state: QuestionComposerState) -> Dict[str, Any]:
		"""Generates an initial set of questions using an LLM."""
		print('Node: _generate_initial_questions_node')
		messages = state.get('messages', [])
		messages.append(AIMessage(content=get_translation(self.lang, 'info_generating_initial_questions')))

		user_characteristics = state.get('user_characteristics')
		knowledge_context_dict = state.get('knowledge_context', {'knowledge': 'No specific context retrieved.', 'sources': []})
		num_questions = state.get('num_questions_to_generate', 15)

		if not user_characteristics or not user_characteristics.characteristics:
			print('Error: User characteristics not found.')
			return {'error': _('error_missing_user_characteristics', self.lang), 'messages': messages}

		try:
			prompt_str = prompt.GENERATE_INITIAL_QUESTIONS_PROMPT.format(
				user_characteristics=str(user_characteristics.characteristics),
				knowledge_context=knowledge_context_dict.get('knowledge', 'No specific context.'),
				num_questions_to_generate=num_questions,
			)
			llm_response = await self.llm.ainvoke([HumanMessage(content=prompt_str)])
			generated_text = llm_response.content.strip()

			initial_questions = self._parse_llm_generated_questions(generated_text, category='initial')

			if not initial_questions:
				print('Warning: LLM did not generate any initial questions in the expected format.')
				initial_questions.append(GeneratedQuestion(id='fallback_initial_1', text='What are your key strengths and how do they align with your career goals?', category='fallback'))

			print(f'Generated {len(initial_questions)} initial questions.')
			return {
				'initial_questions': initial_questions,
				'refined_questions': initial_questions,
				'current_iteration': 0,
				'messages': messages + [AIMessage(content=f'Generated {len(initial_questions)} initial questions.')],
			}
		except Exception as e:
			print(f'Error in _generate_initial_questions_node: {e}')
			return {'error': _('error_initial_question_generation_failed', self.lang) + f': {str(e)}', 'messages': messages + [AIMessage(content=f'Error generating initial questions: {str(e)}')]}

	async def _self_reflect_questions_node(self, state: QuestionComposerState) -> Dict[str, Any]:
		"""Evaluates and refines questions using LLM for critique and refinement."""
		print('Node: _self_reflect_questions_node')
		current_questions_generated = state.get('refined_questions', [])
		user_characteristics = state.get('user_characteristics')
		knowledge_context_dict = state.get('knowledge_context', {'knowledge': '', 'sources': []})
		iteration = state.get('current_iteration', 0)
		max_iterations = state.get('max_iterations', 2)
		num_questions_target = state.get('num_questions_to_generate', 15)
		messages = state.get('messages', [])

		messages.append(AIMessage(content=get_translation(self.lang, 'info_self_reflecting_questions', {'iteration_count': iteration + 1, 'max_iterations': max_iterations})))

		if not current_questions_generated:
			print('Warning: No questions to refine.')
			return {'error': _('error_self_reflection_step_failed', self.lang) + ': No questions to reflect upon.', 'messages': messages}

		questions_to_critique_str = '\n'.join([f'{i + 1}. {q.text}' for i, q in enumerate(current_questions_generated)])

		try:
			critique_prompt_str = prompt.CRITIQUE_QUESTIONS_PROMPT.format(
				user_characteristics=str(user_characteristics.characteristics),
				knowledge_context=knowledge_context_dict.get('knowledge', 'No specific context.'),
				generated_questions=questions_to_critique_str,
			)
			critique_response = await self.llm.ainvoke([HumanMessage(content=critique_prompt_str)])
			critique_text = critique_response.content.strip()
			print(f'Critique for iteration {iteration + 1}:\n{critique_text}')

			refine_prompt_str = prompt.REFINE_QUESTIONS_PROMPT.format(
				user_characteristics=str(user_characteristics.characteristics),
				knowledge_context=knowledge_context_dict.get('knowledge', 'No specific context.'),
				generated_questions=questions_to_critique_str,
				critique=critique_text,
				num_questions_to_generate=num_questions_target,
			)
			refine_response = await self.llm.ainvoke([HumanMessage(content=refine_prompt_str)])
			refined_questions_text = refine_response.content.strip()

			newly_refined_questions = self._parse_llm_generated_questions(refined_questions_text, category=f'refined_iter_{iteration + 1}')

			if not newly_refined_questions:
				print(f'Warning: LLM did not generate refined questions in iteration {iteration + 1}. Using previous set.')
				newly_refined_questions = current_questions_generated

			print(f'Refined to {len(newly_refined_questions)} questions in iteration {iteration + 1}.')
			return {
				'refined_questions': newly_refined_questions,
				'critique': critique_text,
				'current_iteration': iteration + 1,
				'messages': messages
				+ [AIMessage(content=f'Self-reflection iteration {iteration + 1} completed. Critique: {critique_text[:100]}... Refined {len(newly_refined_questions)} questions.')],
			}
		except Exception as e:
			print(f'Error in _self_reflect_questions_node (iteration {iteration + 1}): {e}')
			error_msg = _('error_self_reflection_step_failed', self.lang) + f': {str(e)}'
			return {
				'error': error_msg,
				'refined_questions': current_questions_generated,
				'current_iteration': iteration + 1,
				'messages': messages + [AIMessage(content=f'Error during self-reflection iteration {iteration + 1}: {str(e)}')],
			}

	async def _select_final_questions_node(self, state: QuestionComposerState) -> Dict[str, Any]:
		"""Selects the top N critical questions using an LLM."""
		print('Node: _select_final_questions_node')
		messages = state.get('messages', [])
		messages.append(AIMessage(content=get_translation(self.lang, 'info_selecting_final_questions')))

		questions_to_select_from_generated = state.get('refined_questions', [])
		if not questions_to_select_from_generated:
			questions_to_select_from_generated = state.get('initial_questions', [])

		if not questions_to_select_from_generated:
			print('Error: No questions available for final selection.')
			return {'error': _('error_final_question_selection_failed', self.lang) + ': No questions to select from.', 'messages': messages}

		num_final = state.get('num_final_questions', 10)
		user_characteristics = state.get('user_characteristics')

		available_questions_str = '\n'.join([f'{i + 1}. {q.text}' for i, q in enumerate(questions_to_select_from_generated)])

		try:
			prompt_str = prompt.SELECT_FINAL_QUESTIONS_PROMPT.format(
				user_characteristics=str(user_characteristics.characteristics), generated_questions=available_questions_str, num_final_questions=num_final
			)
			llm_response = await self.llm.ainvoke([HumanMessage(content=prompt_str)])
			selected_questions_text = llm_response.content.strip()

			final_selected_questions = self._parse_llm_generated_questions(selected_questions_text, category='final_selection')

			final_selected_questions = final_selected_questions[:num_final]

			if not final_selected_questions and questions_to_select_from_generated:
				print(f'Warning: LLM failed to select final questions. Taking first {num_final} from available.')
				final_selected_questions = questions_to_select_from_generated[:num_final]

			print(f'Selected {len(final_selected_questions)} final questions.')
			return {'final_questions': final_selected_questions, 'messages': messages + [AIMessage(content=f'Selected {len(final_selected_questions)} final questions.')]}
		except Exception as e:
			print(f'Error in _select_final_questions_node: {e}')
			error_msg = _('error_final_question_selection_failed', self.lang) + f': {str(e)}. Using fallback selection.'
			fallback_selection = questions_to_select_from_generated[:num_final]
			return {
				'final_questions': fallback_selection,
				'error': error_msg,
				'messages': messages + [AIMessage(content=f'Error selecting final questions: {str(e)}. Selected {len(fallback_selection)} questions as fallback.')],
			}

	# --- Conditional Edges ---
	def _should_continue_self_reflection(self, state: QuestionComposerState) -> str:
		"""Determines if the self-reflection loop should continue."""
		print('Conditional: _should_continue_self_reflection')
		current_iter = state.get('current_iteration', 0)
		max_iter = state.get('max_iterations', 2)

		if state.get('error') and _('error_self_reflection_step_failed', self.lang) in state.get('error', ''):
			print(f'Error detected during self-reflection: {state.get("error")}. Ending reflection loop.')
			return 'select_final_questions'

		if current_iter < max_iter:
			print(f'Iteration {current_iter + 1}/{max_iter}. Continuing self-reflection.')
			return 'self_reflect_questions'
		else:
			print(f'Max iterations ({max_iter}) reached. Proceeding to final selection.')
			return 'select_final_questions'

	def _decide_after_knowledge_query(self, state: QuestionComposerState) -> str:
		"""Decides next step after querying knowledge base."""
		print('Conditional: _decide_after_knowledge_query')
		if state.get('error') and _('error_knowledge_base_query_failed', self.lang) in state.get('error', ''):
			print('Error connecting to knowledge base. Proceeding to generate initial questions with error context.')
		return 'generate_initial_questions'

	def _build_graph(self) -> StateGraph:
		"""Constructs the LangGraph StateGraph for question composition."""
		graph = StateGraph(QuestionComposerState)

		graph.add_node('prepare_knowledge_query', self._prepare_knowledge_query_node)
		graph.add_node('query_knowledge_base', self._query_knowledge_base_node)
		graph.add_node('generate_initial_questions', self._generate_initial_questions_node)
		graph.add_node('self_reflect_questions', self._self_reflect_questions_node)
		graph.add_node('select_final_questions', self._select_final_questions_node)

		graph.set_entry_point('prepare_knowledge_query')
		graph.add_edge('prepare_knowledge_query', 'query_knowledge_base')

		graph.add_conditional_edges('query_knowledge_base', self._decide_after_knowledge_query, {'generate_initial_questions': 'generate_initial_questions'})

		graph.add_edge('generate_initial_questions', 'self_reflect_questions')

		graph.add_conditional_edges(
			'self_reflect_questions', self._should_continue_self_reflection, {'self_reflect_questions': 'self_reflect_questions', 'select_final_questions': 'select_final_questions'}
		)
		graph.add_edge('select_final_questions', END)

		print('QuestionComposerGraph: Graph built.')
		return graph.compile(checkpointer=self.memory)

	async def compose(self, user_input_data: Dict[str, Any], max_iterations: int = 2, num_questions_to_generate: int = 15, num_final_questions: int = 10) -> Dict[str, Any]:
		"""Runs the question composition workflow."""
		print(f'Starting question composition workflow for user_input: {user_input_data}')

		user_characteristics_model = UserCharacteristics(characteristics=user_input_data)

		initial_state: QuestionComposerState = {
			'user_characteristics': user_characteristics_model,
			'knowledge_query': None,
			'knowledge_context': None,
			'initial_questions': [],
			'critique': None,
			'refined_questions': [],
			'final_questions': [],
			'current_iteration': 0,
			'max_iterations': max_iterations,
			'num_questions_to_generate': num_questions_to_generate,
			'num_final_questions': num_final_questions,
			'messages': [SystemMessage(content='Question Composer Agent Initialized'), HumanMessage(content=f'User characteristics: {user_input_data}')],
			'error': None,
		}

		session_id = str(uuid.uuid4())
		config = {'configurable': {'session_id': session_id}}

		try:
			final_state_result = await self.workflow.ainvoke(initial_state, config=config)
			print(f'Workflow completed. Final state result: {final_state_result}')

			error_message = final_state_result.get('error')
			if error_message:
				print(f'Error during workflow execution: {error_message}')

			output_questions_generated = final_state_result.get('final_questions', [])
			output_questions_text = [q.text for q in output_questions_generated]

			return {
				'final_questions': output_questions_text,
				'user_characteristics_processed': final_state_result.get('user_characteristics').characteristics,
				'knowledge_summary': final_state_result.get('knowledge_context', {}).get('knowledge', 'N/A')[:200] + '...',
				'iterations_done': final_state_result.get('current_iteration', 0),
				'messages': [msg.content if hasattr(msg, 'content') else str(msg) for msg in final_state_result.get('messages', [])],
				'error': error_message,
			}

		except Exception as e:
			print(f'Exception during QuestionComposerGraph.compose: {e}')
			translated_error = get_translation(self.lang, 'error_composer_graph_execution') + f': {str(e)}'
			return {'final_questions': [], 'error': translated_error, 'messages': initial_state.get('messages', []) + [AIMessage(content=f'Critical error in graph execution: {str(e)}')]}


def get_translation(lang: str, key: str, params: Optional[Dict[str, Any]] = None) -> str:
	_translations = {
		'en': {
			'info_preparing_knowledge_query': 'Preparing query for knowledge base...',
			'info_querying_knowledge_base': 'Querying knowledge base for relevant context...',
			'info_generating_initial_questions': 'Generating initial set of questions...',
			'info_self_reflecting_questions': 'Performing self-reflection on generated questions (Iteration {iteration_count}/{max_iterations})...',
			'info_selecting_final_questions': 'Selecting final questions...',
			'error_missing_user_characteristics': 'User characteristics are required.',
			'error_knowledge_query_failed': 'Failed to prepare knowledge query.',
			'error_knowledge_base_query_failed': 'Failed to query knowledge base.',
			'error_initial_question_generation_failed': 'Failed to generate initial questions.',
			'error_self_reflection_step_failed': 'Self-reflection step failed.',
			'error_final_question_selection_failed': 'Failed to select final questions.',
			'error_llm_initialization': 'Failed to initialize the language model.',
			'error_composer_graph_execution': 'A critical error occurred in the question composer graph execution',
		},
	}

	text = _translations.get(lang, _translations['en']).get(key, key)
	if params:
		try:
			text = text.format(**params)
		except KeyError:
			pass
	return text
