"""
Question Generation Workflow using LangGraph.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.modules.question_interview.workflows.question_generation.state.workflow_state import (
	QuestionGenerationState,
)
from app.modules.question_interview.workflows.question_generation.config.workflow_config import (
	QuestionGenerationWorkflowConfig,
)
from app.modules.question_interview.workflows.question_generation.config.prompts import (
	QUESTION_GENERATION_SYSTEM_PROMPT,
	ANALYSIS_SYSTEM_PROMPT,
	ROUTER_PROMPT,
)
from app.modules.question_interview.schemas.interview_schemas import (
	Question,
	UserProfile,
	AnalysisDecision,
	QuestionGenerationResponse,
)

logger = logging.getLogger(__name__)


class QuestionGenerationWorkflow:
	"""
	LangGraph workflow để tạo câu hỏi khảo sát thông minh.

	Workflow bao gồm:
	1. Analyze User Info - Phân tích thông tin người dùng hiện có
	2. Generate Questions - Tạo 4 câu hỏi mới
	3. Router - Quyết định tiếp tục hay dừng lại
	"""

	def __init__(self, config: Optional[QuestionGenerationWorkflowConfig] = None):
		self.config = config or QuestionGenerationWorkflowConfig.from_env()
		self.llm = ChatGoogleGenerativeAI(
			model=self.config.model_name,
			temperature=self.config.temperature,
			max_tokens=self.config.max_tokens,
		)

		# Setup parsers
		self.question_parser = PydanticOutputParser(pydantic_object=QuestionGenerationResponse)
		self.analysis_parser = PydanticOutputParser(pydantic_object=AnalysisDecision)

		# Build workflow
		self.workflow = self._build_workflow()
		self.checkpointer = MemorySaver()
		self.compiled_workflow = self.workflow.compile(checkpointer=self.checkpointer)

		logger.info('QuestionGenerationWorkflow initialized successfully')

	def _build_workflow(self) -> StateGraph:
		"""Build the LangGraph workflow"""
		workflow = StateGraph(QuestionGenerationState)

		# Add nodes
		workflow.add_node('analyze_user_info', self._analyze_user_info)
		workflow.add_node('generate_questions', self._generate_questions)
		workflow.add_node('router', self._router)

		# Add edges
		workflow.set_entry_point('analyze_user_info')
		workflow.add_edge('analyze_user_info', 'router')
		workflow.add_edge('generate_questions', 'analyze_user_info')

		# Conditional routing
		workflow.add_conditional_edges(
			'router',
			self._should_continue,
			{'continue': 'generate_questions', 'end': END},
		)

		return workflow

	async def _analyze_user_info(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Phân tích thông tin người dùng và quyết định có cần thêm câu hỏi không"""
		logger.info(f'Analyzing user info - Iteration {state["current_iteration"]}')

		try:
			# Prepare analysis prompt
			analysis_prompt = ChatPromptTemplate.from_messages([
				('system', ANALYSIS_SYSTEM_PROMPT),
				(
					'user',
					"""
Phân tích thông tin người dùng hiện có:

THÔNG TIN NGƯỜI DÙNG:
{user_data}

CÁC CÂU HỎI ĐÃ HỎI:
{previous_questions}

Hãy đánh giá mức độ đầy đủ thông tin và quyết định có cần hỏi thêm không.

{format_instructions}
""",
				),
			])

			# Format previous questions
			previous_q_text = '\n'.join([f'- {q["Question"]}' if isinstance(q, dict) and "Question" in q else f'- {q.Question}' if hasattr(q, 'Question') else ''
				for q in state['all_previous_questions'] if isinstance(q, (dict, Question))]) if state['all_previous_questions'] else 'Chưa có câu hỏi nào'

			# Run analysis
			chain = analysis_prompt | self.llm | self.analysis_parser
			analysis_result = await chain.ainvoke({
				'user_data': state['user_profile'].model_dump(),
				'previous_questions': previous_q_text,
				'format_instructions': self.analysis_parser.get_format_instructions(),
			})

			logger.info(f'Analysis completed - Decision: {analysis_result.decision}, Score: {analysis_result.completeness_score}')

			return {
				'analysis_decision': analysis_result,
				'completeness_score': analysis_result.completeness_score,
				'missing_areas': analysis_result.missing_areas,
				'focus_areas': analysis_result.suggested_focus,
				'should_continue': analysis_result.decision == 'need_more_info' and state['current_iteration'] < state['max_iterations'],
			}

		except Exception as e:
			logger.error(f'Error in analyze_user_info: {str(e)}')
			return {
				'analysis_decision': AnalysisDecision(
					decision='need_more_info',
					missing_areas=['general_info'],
					reasoning=f'Analysis failed: {str(e)}',
					completeness_score=0.0,
					suggested_focus=['skills', 'goals'],
				),
				'should_continue': False,
				'error_message': str(e),
			}

	async def _generate_questions(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Tạo 4 câu hỏi mới dựa trên phân tích"""
		logger.info(f'Generating questions - Focus areas: {state["focus_areas"]}')

		try:
			# Prepare generation prompt
			generation_prompt = ChatPromptTemplate.from_messages([
				('system', QUESTION_GENERATION_SYSTEM_PROMPT),
				(
					'user',
					"""
Tạo 4 câu hỏi mới để bổ sung thông tin người dùng:

THÔNG TIN HIỆN TẠI:
{user_data}

CÁC LĨNH VỰC CẦN TẬP TRUNG:
{focus_areas}

CÁC CÂU HỎI ĐÃ HỎI (tránh lặp lại):
{previous_questions}

YÊU CẦU:
- Tạo đúng 4 câu hỏi: 1 single_option, 1 multiple_choice, 1 text_input, 1 sub_form
- Tập trung vào các lĩnh vực: {focus_areas}
- Không lặp lại nội dung đã hỏi
- Sử dụng tiếng Việt tự nhiên

{format_instructions}
""",
				),
			])

			# Format data
			all_prev_qs = state.get('all_previous_questions')
			if not all_prev_qs:
				all_prev_qs = []
			previous_q_text = '\n'.join([
				f'- {q["Question"]}' if isinstance(q, dict) and "Question" in q else f'- {q.Question}' if hasattr(q, 'Question') else ''
				for q in all_prev_qs if isinstance(q, (dict, Question))]) if all_prev_qs else 'Chưa có'

			focus_text = ', '.join(state['focus_areas']) if state['focus_areas'] else 'Thông tin tổng quát'

			# Run generation
			chain = generation_prompt | self.llm | self.question_parser
			result = await chain.ainvoke({
				'user_data': state['user_profile'].model_dump(),
				'focus_areas': focus_text,
				'previous_questions': previous_q_text,
				'format_instructions': self.question_parser.get_format_instructions(),
			})

			# Convert dicts to Question objects if needed
			new_questions = []
			for q in getattr(result, 'questions', []):
				if isinstance(q, Question):
					new_questions.append(q)
				elif isinstance(q, dict):
					try:
						new_questions.append(Question(**q))
					except Exception as e:
						logger.warning(f"Invalid question dict from LLM: {q} ({e})")
				else:
					logger.warning(f"Skipping invalid question (not dict or Question): {q}")
			# Filter out any with missing required fields
			new_questions = [q for q in new_questions if hasattr(q, 'id') and hasattr(q, 'Question') and hasattr(q, 'Question_type') and hasattr(q, 'Question_data') and q.id and q.Question and q.Question_type and q.Question_data is not None]
			if not new_questions:
				if not state['cv_data'] or (isinstance(state['cv_data'], dict) and not any(state['cv_data'].values())):
					# No CV: fallback to orientation questions
					orientation_questions = [
						Question(
							id="orientation_1",
							Question="Bạn đang tìm kiếm công việc trong lĩnh vực nào?",
							Question_type="text_input",
							subtitle="Giúp chúng tôi hiểu định hướng nghề nghiệp của bạn.",
							Question_data=[],
						),
						Question(
							id="orientation_2",
							Question="Vị trí công việc bạn mong muốn là gì?",
							Question_type="text_input",
							subtitle="Chia sẻ vai trò hoặc vị trí bạn hướng tới.",
							Question_data=[],
						),
					]
					new_questions = orientation_questions
				else:
					logger.error("LLM did not return valid questions for provided CV data.")
					raise ValueError("Failed to generate valid questions from LLM output.")
			logger.info(f'Generated {len(new_questions)} questions')

			# Create generation history entry
			history_entry = {
				'iteration': state['current_iteration'],
				'focus_areas': state['focus_areas'],
				'questions_generated': [q.model_dump() for q in new_questions],
				'completeness_before': state['completeness_score'],
			}

			return {
				'generated_questions': new_questions,
				'all_previous_questions': state['all_previous_questions'] + new_questions,
				'current_iteration': state['current_iteration'] + 1,
				'total_questions_generated': state['total_questions_generated'] + len(new_questions),
				'generation_history': state['generation_history'] + [history_entry],
			}

		except Exception as e:
			logger.error(f'Error in generate_questions: {str(e)}')
			return {'error_message': str(e), 'should_continue': False}

	async def _router(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Router node - quyết định tiếp tục hay dừng"""
		decision = state.get('analysis_decision')
		current_iteration = state.get('current_iteration', 0)
		max_iterations = state.get('max_iterations', 5)

		if not decision:
			return {'should_continue': False, 'workflow_complete': True}

		should_continue = decision.decision == 'need_more_info' and current_iteration < max_iterations and not state.get('error_message')

		logger.info(f'Router decision - Continue: {should_continue}, Iteration: {current_iteration}/{max_iterations}')

		return {
			'should_continue': should_continue,
			'workflow_complete': not should_continue,
		}

	def _should_continue(self, state: QuestionGenerationState) -> str:
		"""Conditional routing logic"""
		return 'continue' if state.get('should_continue', False) else 'end'

	async def _generate_orientation_questions(self, state: QuestionGenerationState) -> dict:
		"""Generate 2 orientation questions for users without CV data."""
		logger.info('Generating orientation questions (no CV provided)')
		orientation_questions = [
			Question(
				id="orientation_1",
				Question="Bạn đang tìm kiếm công việc trong lĩnh vực nào?",
				Question_type="text_input",
				subtitle="Giúp chúng tôi hiểu định hướng nghề nghiệp của bạn.",
				Question_data=[],
			),
			Question(
				id="orientation_2",
				Question="Vị trí công việc bạn mong muốn là gì?",
				Question_type="text_input",
				subtitle="Chia sẻ vai trò hoặc vị trí bạn hướng tới.",
				Question_data=[],
			),
		]
		return {
			'generated_questions': orientation_questions,
			'all_previous_questions': state['all_previous_questions'] + orientation_questions,
			'current_iteration': state['current_iteration'] + 1,
			'total_questions_generated': state['total_questions_generated'] + len(orientation_questions),
			'generation_history': state['generation_history'] + [{
				'iteration': state['current_iteration'],
				'focus_areas': ['career_goals', 'interests'],
				'questions_generated': [q.model_dump() for q in orientation_questions],
				'completeness_before': state['completeness_score'],
			}],
		}

	async def generate_questions(
		self,
		user_profile: Optional[UserProfile] = None,
		existing_questions: Optional[List[Question]] = None,
		session_id: Optional[str] = None,
		cv_data: Optional[Dict[str, Any]] = None,  # Accept cv_data directly for flexibility
	) -> QuestionGenerationResponse:
		"""
		Main method để generate questions, updated for JD alignment support.
		"""
		logger.info('Starting question generation workflow')

		# Use cv_data if provided, else fallback to user_profile
		effective_cv_data = cv_data if cv_data is not None else (user_profile.model_dump() if user_profile else {})

		# Prepare initial state
		initial_state: QuestionGenerationState = {
			'user_profile': user_profile or UserProfile(),
			'cv_data': effective_cv_data,
			'generated_questions': [],
			'all_previous_questions': existing_questions or [],
			'current_iteration': 0,
			'max_iterations': self.config.max_iterations,
			'analysis_decision': None,
			'completeness_score': 0.0,
			'missing_areas': [],
			'focus_areas': [],
			'should_continue': True,
			'workflow_complete': False,
			'error_message': None,
			'generation_history': [],
			'total_questions_generated': 0,
			'session_id': session_id,
		}

		# --- JD Alignment Logic ---
		try:
			if not effective_cv_data or (isinstance(effective_cv_data, dict) and not any(effective_cv_data.values())):
				# No CV provided: generate 2 orientation questions
				orientation_result = await self._generate_orientation_questions(initial_state)
				focus_areas = ['career_goals', 'interests']
				return QuestionGenerationResponse(
					questions=orientation_result['generated_questions'],
					analysis="Định hướng nghề nghiệp và sở thích cá nhân.",
					next_focus_areas=focus_areas,
					completeness_score=0.2,
					should_continue=True,
				)

			# If JD alignment is present, use it for focus_areas and early exit
			jd_alignment = effective_cv_data.get('jd_alignment')
			if jd_alignment:
				# Example structure: {'alignment_score': 0.75, 'misaligned_areas': ['skills', 'experience']}
				alignment_score = jd_alignment.get('alignment_score', 0.0)
				misaligned_areas = jd_alignment.get('misaligned_areas', [])
				logger.info(f"JD alignment found: score={alignment_score}, misaligned_areas={misaligned_areas}")
				# If alignment >= 0.8, allow early exit
				if alignment_score >= 0.8:
					return QuestionGenerationResponse(
						questions=[],
						analysis="Ứng viên phù hợp với JD (>=80%). Không cần thêm câu hỏi.",
						next_focus_areas=[],
						completeness_score=alignment_score,
						should_continue=False,
					)
				# Otherwise, focus questions on misaligned areas
				initial_state['focus_areas'] = misaligned_areas or []
				config = {'configurable': {'thread_id': session_id or 'default'}}
				final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)
				return QuestionGenerationResponse(
					questions=final_state.get('generated_questions', []),
					analysis=final_state.get('analysis_decision', {}).reasoning,
					next_focus_areas=final_state.get('focus_areas', []),
					completeness_score=alignment_score,
					should_continue=final_state.get('should_continue', False),
				)
			else:
				# No JD alignment, fallback to old logic
				config = {'configurable': {'thread_id': session_id or 'default'}}
				final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)
				return QuestionGenerationResponse(
					questions=final_state.get('generated_questions', []),
					analysis=final_state.get('analysis_decision', {}).reasoning,
					next_focus_areas=final_state.get('focus_areas', []),
					completeness_score=final_state.get('completeness_score', 0.0),
					should_continue=final_state.get('should_continue', False),
				)
		except Exception as e:
			logger.error(f"Error in JD alignment logic: {e}. Fallback to old flow.")
			# Fallback to old logic
			config = {'configurable': {'thread_id': session_id or 'default'}}
			final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)
			return QuestionGenerationResponse(
				questions=final_state.get('generated_questions', []),
				analysis=final_state.get('analysis_decision', {}).reasoning,
				next_focus_areas=final_state.get('focus_areas', []),
				completeness_score=final_state.get('completeness_score', 0.0),
				should_continue=final_state.get('should_continue', False),
			)

	async def analyze_user_completeness(self, user_profile: UserProfile, previous_questions: List[Question] = None) -> Dict[str, Any]:
		"""
		Analyze user profile completeness without generating new questions.
		"""
		try:
			# Prepare analysis prompt
			analysis_prompt = ChatPromptTemplate.from_messages([
				('system', ANALYSIS_SYSTEM_PROMPT),
				(
					'user',
					"""
Phân tích thông tin người dùng hiện có:

THÔNG TIN NGƯỜI DÙNG:
{user_data}

CÁC CÂU HỎI ĐÃ HỎI:
{previous_questions}

Hãy đánh giá mức độ đầy đủ thông tin.

{format_instructions}
""",
				),
			])

			# Format previous questions
			previous_q_text = '\n'.join([f'- {q.Question} ({q.Question_type})' for q in (previous_questions or [])]) if previous_questions else 'Chưa có câu hỏi nào'

			# Run analysis
			chain = analysis_prompt | self.llm | self.analysis_parser
			analysis_result = await chain.ainvoke({
				'user_data': user_profile.model_dump(),
				'previous_questions': previous_q_text,
				'format_instructions': self.analysis_parser.get_format_instructions(),
			})

			return {
				'completeness_score': analysis_result.completeness_score,
				'missing_areas': analysis_result.missing_areas,
				'analysis': analysis_result.reasoning,
				'should_continue': analysis_result.decision == 'need_more_info',
			}

		except Exception as e:
			logger.error(f'Error analyzing user completeness: {str(e)}')
			return {
				'completeness_score': 0.0,
				'missing_areas': ['general_info'],
				'analysis': f'Analysis failed: {str(e)}',
				'should_continue': True,
			}

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""
		return {
			'name': 'Question Generation Workflow',
			'version': '1.0.0',
			'config': self.config.to_dict(),
			'nodes': ['analyze_user_info', 'generate_questions', 'router'],
			'max_iterations': self.config.max_iterations,
			'question_types': [
				'single_option',
				'multiple_choice',
				'text_input',
				'sub_form',
			],
		}


# Factory function
def create_question_generation_workflow(
	config: Optional[QuestionGenerationWorkflowConfig] = None,
) -> QuestionGenerationWorkflow:
	"""Create question generation workflow instance"""
	return QuestionGenerationWorkflow(config)


logger.info('Question Generation Workflow module loaded!')
