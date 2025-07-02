"""
Question Generation Workflow using LangGraph.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import StrOutputParser
import json
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
		self.question_parser = StrOutputParser()
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
			# Format previous questions
			previous_q_text = '\n'.join([
				f'- {q["Question"]}' if isinstance(q, dict) and "Question" in q
				else f'- {getattr(q, "Question", "")}' if hasattr(q, 'Question')
				else ''
				for q in state.get('all_previous_questions', [])
				if (isinstance(q, dict) and "Question" in q) or hasattr(q, 'Question')
			])
			if not previous_q_text.strip():
				previous_q_text = 'Chưa có câu hỏi nào'

			# Prompt setup
			user_prompt = f"""
			Trước tiên, hãy **tóm tắt CV** trong 2–3 câu để giúp quá trình phân tích chính xác hơn.

			Sau đó, **phân tích mức độ đầy đủ** của hồ sơ người dùng dựa trên các thông tin sau:

			--- CV ĐÃ LÀM SẠCH ---
			{state.get('cv_text', '')}

			--- MÔ TẢ CÔNG VIỆC ---
			{state.get('job_description', '')}

			--- CÁC CÂU HỎI ĐÃ HỎI ---
			{json.dumps([
			  {"question": q["Question"] if isinstance(q, dict) else getattr(q, "Question", ""),
			   "answer": q.get("answer") if isinstance(q, dict) else getattr(q, "answer", "")}
			  for q in state.get("all_previous_questions", [])
			], ensure_ascii=False, indent=2)}

			{self.analysis_parser.get_format_instructions()}
			"""

			full_prompt = f"{ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}".replace("{", "{{").replace("}", "}}")
			analysis_prompt = PromptTemplate(input_variables=[], template=full_prompt)

			chain = analysis_prompt | self.llm | self.analysis_parser
			analysis_result = await chain.ainvoke({})

			logger.info(
				f'Analysis completed - Decision: {analysis_result.decision}, Score: {analysis_result.completeness_score}')

			return {
				'analysis_decision': analysis_result,
				'completeness_score': analysis_result.completeness_score,
				'missing_areas': analysis_result.missing_areas,
				'focus_areas': analysis_result.suggested_focus,
				'should_continue': state['current_iteration'] < state['max_iterations'],
				'cv_summary': analysis_result.cv_summary,
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
		logger.info(f'Generating questions - Iteration {state["current_iteration"]}')

		try:
			# Format previous questions
			previous_q_text = '\n'.join([
				f'- {q["Question"]}' if isinstance(q, dict) and "Question" in q
				else f'- {getattr(q, "Question", "")}' if hasattr(q, 'Question')
				else ''
				for q in state.get('all_previous_questions', [])
				if (isinstance(q, dict) and "Question" in q) or hasattr(q, 'Question')
			])
			if not previous_q_text.strip():
				previous_q_text = 'Chưa có'

			user_prompt = f"""
			TRẢ LỜI DUY NHẤT BẰNG JSON THÔ. KHÔNG GIẢI THÍCH. KHÔNG VIẾT GÌ NGOÀI JSON. CHỈ JSON.

			Please generate exactly one question in JSON format using the structure below:

			{{
			  "questions": [
			    {{
			      "id": "string",
			      "Question": "string",
			      "Question_type": "text_input",
			      "subtitle": "string or null",
			      "Question_data": []
			    }}
			  ]
			}}

			--- CLEANED CV ---
			{state.get('cv_text', '')}

			--- JOB DESCRIPTION ---
			{state.get('job_description', '')}

			--- PREVIOUS QUESTIONS ---
			{json.dumps([
			  {"question": q["Question"] if isinstance(q, dict) else getattr(q, "Question", ""),
			   "answer": q.get("answer") if isinstance(q, dict) else getattr(q, "answer", "")}
			  for q in state.get("all_previous_questions", [])
			], ensure_ascii=False, indent=2)}

			--- FOCUS AREAS ---
			{state.get('focus_areas', [])}
			"""

			# Merge system + user prompt into one long string and escape braces
			full_prompt = f"""{QUESTION_GENERATION_SYSTEM_PROMPT}\n\n{user_prompt}""".replace("{", "{{").replace("}",
																												 "}}")

			# Then define a prompt template that takes NO variables
			generation_prompt = PromptTemplate(input_variables=[], template=full_prompt)

			# Chain as usual
			chain = generation_prompt | self.llm | self.question_parser
			raw_output = await chain.ainvoke({})
			logger.error(f"[LLM RAW OUTPUT] ===\n{raw_output}\n===")

			# Strip markdown-style formatting
			if raw_output.strip().startswith("```json"):
				raw_output = raw_output.strip().removeprefix("```json").removesuffix("```").strip()
			elif raw_output.strip().startswith("```"):
				raw_output = raw_output.strip().removeprefix("```").removesuffix("```").strip()

			if not raw_output.strip():
				raise ValueError("LLM returned empty output.")

			try:
				parsed = json.loads(raw_output)
				question_dicts = parsed.get("questions", [])
			except Exception as e:
				logger.error(f"Failed to parse question JSON: {e}\nRAW OUTPUT:\n{raw_output}")
				raise ValueError("Failed to generate valid questions from LLM output.")

			new_questions = []
			for q in question_dicts:
				try:
					new_questions.append(Question(**q))
				except Exception as e:
					logger.warning(f"Invalid question from LLM: {q} ({e})")

			new_questions = [q for q in new_questions if
							 hasattr(q, 'id') and q.id and q.Question and q.Question_data is not None]
			# Keep all valid new questions
			new_questions = [q for q in new_questions if q.id and q.Question and q.Question_data is not None]

			if not new_questions:
				logger.error("LLM did not return valid questions.")
				raise ValueError("Failed to generate valid questions from LLM output.")

			logger.info(f'Generated {len(new_questions)} questions')

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
				'last_question_id': new_questions[0].id if new_questions else None,
			}

		except Exception as e:
			logger.error(f'Error in generate_questions: {str(e)}')
			return {'error_message': str(e), 'should_continue': False}

	async def _router(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Router node - quyết định tiếp tục hay dừng"""
		decision = state.get('analysis_decision')

		if not decision:
			return {'should_continue': False, 'workflow_complete': True}

		should_continue = (
				state.get('should_continue', False)
				and state.get('current_iteration', 0) < state.get('max_iterations', 5)
		)


		return {
			'should_continue': should_continue,
			'workflow_complete': not should_continue,
		}

	def _should_continue(self, state: QuestionGenerationState) -> str:
		if state.get('current_iteration', 0) >= state.get('max_iterations', 5):
			return 'end'
		return 'continue' if state.get('should_continue', False) else 'end'

# Factory function
def create_question_generation_workflow(
	config: Optional[QuestionGenerationWorkflowConfig] = None,
) -> QuestionGenerationWorkflow:
	"""Create question generation workflow instance"""
	return QuestionGenerationWorkflow(config)


logger.info('Question Generation Workflow module loaded!')
