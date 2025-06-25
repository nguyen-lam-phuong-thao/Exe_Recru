"""
Question composer repository layer.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from langgraph.checkpoint.memory import MemorySaver

from app.exceptions.exception import NotFoundException, ValidationException, CustomHTTPException
from app.middleware.translation_manager import _

from ..workflows.question_generation import QuestionGenerationWorkflow
from ..workflows.question_generation.config.workflow_config import QuestionGenerationWorkflowConfig
from ..schemas.interview_request import QuestionGenerationRequest, AnalyzeUserProfileRequest, SearchQuestionSessionsRequest
from ..schemas.interview_response import QuestionGenerationResponse, UserProfileAnalysisResponse, QuestionSessionResponse
from ..schemas.interview_schemas import UserProfile, Question

logger = logging.getLogger(__name__)


class InterviewComposerRepo:
	"""
	Repository layer for question composer module.

	Handles business logic for question generation and user profile analysis.
	"""

	def __init__(self):
		logger.info('Initializing InterviewComposerRepo (in-memory)')
		self.memory = MemorySaver()
		self.config = QuestionGenerationWorkflowConfig.from_env()
		self.workflow = QuestionGenerationWorkflow(self.config)
		self.compiled_workflow = self.workflow.workflow.compile(checkpointer=self.memory)
		logger.info('InterviewComposerRepo initialized (in-memory)')

	async def generate_questions(self, request: QuestionGenerationRequest) -> QuestionGenerationResponse:
		"""
		Generate intelligent questions based on user profile and history.
		"""
		logger.info('Starting question generation process (in-memory)')
		session_id = request.session_id or str(uuid.uuid4())
		logger.info(f'Using session_id: {session_id}')
		user_profile = UserProfile(**(request.cv_data or {}))
		previous_questions = [Question(**q) for q in (request.previous_questions or [])]
		# Build initial state if new session
		state = await self.memory.get(session_id)
		if not state:
			state = {
				'user_profile': user_profile,
				'cv_data': request.cv_data or {},
				'generated_questions': [],
				'all_previous_questions': previous_questions,
				'current_iteration': 0,
				'max_iterations': request.max_iterations or 5,
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
			# Save initial state
			await self.compiled_workflow.ainvoke(state, config={"configurable": {"session_id": session_id}})
		# Run workflow for this session
		result = await self.compiled_workflow.ainvoke(state, config={"configurable": {"session_id": session_id}})
		# Save updated state
		await self.memory.put(session_id, result)
		# Build response
		return QuestionGenerationResponse(
			session_id=session_id,
			questions=result.get('generated_questions', []),
			analysis=str(result.get('analysis_decision', '')),
			next_focus_areas=result.get('focus_areas', []),
			completeness_score=result.get('completeness_score', 0.0),
			should_continue=result.get('should_continue', True),
			current_iteration=result.get('current_iteration', 0),
			total_questions_generated=result.get('total_questions_generated', 0),
		)

	async def analyze_user_profile(self, request: AnalyzeUserProfileRequest) -> UserProfileAnalysisResponse:
		"""
		Analyze user profile completeness without generating new questions.
		"""
		logger.info('Starting user profile analysis')
		logger.info(f'Analysis request - User profile provided: {bool(request.user_profile)}, Previous questions count: {len(request.previous_questions or [])}')

		try:
			# Validate request
			logger.info('Validating analysis request')
			if not request.user_profile:
				logger.warning('User profile is required but not provided')
				raise ValidationException(_('user_profile_required'))

			logger.info('Request validation passed')

			# Prepare user profile
			logger.info('Preparing user profile for analysis')
			logger.info(f'User profile data keys: {list(request.user_profile.keys())}')
			user_profile = UserProfile(**request.user_profile)
			logger.info('User profile object created successfully')

			# Convert previous questions
			logger.info('Processing previous questions for analysis')
			previous_questions = []
			if request.previous_questions:
				logger.info(f'Converting {len(request.previous_questions)} previous questions')
				previous_questions = [Question(**q) for q in request.previous_questions]
				logger.info(f'Successfully converted {len(previous_questions)} questions')

				# Log question type distribution
				question_types = {}
				for q in previous_questions:
					question_types[q.Question_type] = question_types.get(q.Question_type, 0) + 1
				logger.info(f'Question type distribution: {question_types}')
			else:
				logger.info('No previous questions to analyze')

			# Use workflow for analysis
			temp_state = {
				'user_profile': user_profile,
				'cv_data': {},
				'generated_questions': [],
				'all_previous_questions': previous_questions,
				'current_iteration': 0,
				'max_iterations': 1,
				'analysis_decision': None,
				'completeness_score': 0.0,
				'missing_areas': [],
				'focus_areas': [],
				'should_continue': True,
				'workflow_complete': False,
				'error_message': None,
				'generation_history': [],
				'total_questions_generated': 0,
				'session_id': str(uuid.uuid4()),
			}
			result = await self.compiled_workflow.ainvoke(temp_state)

			logger.info('Profile analysis completed successfully')
			logger.info(f'Analysis results summary:')
			logger.info(f'Completeness score: {result.get("completeness_score", 0.0):.3f}')
			logger.info(f'Missing areas count: {len(result.get("missing_areas", []))}')
			logger.info(f'Analysis length: {len(result.get("analysis_decision", ""))} characters')
			logger.info(f'Should continue: {result.get("should_continue", True)}')

			missing_areas = result.get('missing_areas', [])
			if missing_areas:
				logger.info(f'Missing areas: {missing_areas}')
			else:
				logger.info('No missing areas identified')

			response = UserProfileAnalysisResponse(
				completeness_score=result.get('completeness_score', 0.0),
				missing_areas=missing_areas,
				analysis=str(result.get('analysis_decision', '')),
				should_continue=result.get('should_continue', True),
			)

			logger.info(f'User profile analysis completed successfully!')
			logger.info(f'Final analysis score: {response.completeness_score:.3f}')

			return response

		except ValidationException as e:
			logger.error(f'Validation error in profile analysis: {str(e)}')
			raise
		except Exception as e:
			logger.error(f'Unexpected error in profile analysis: {str(e)}', exc_info=True)
			raise CustomHTTPException(message=_('profile_analysis_failed'))

	async def get_question_session(self, session_id: str) -> Dict[str, Any]:
		"""
		Get question session by ID.
		"""
		logger.info(f'Retrieving question session: {session_id}')

		state = await self.memory.get(session_id)
		if not state:
			logger.warning(f'Session not found: {session_id}')
			raise NotFoundException(_('session_not_found'))

		logger.info(f'Session found - ID: {session_id}, Status: {state.get("status", "N/A")}, Iteration: {state.get("current_iteration", "N/A")}/{state.get("max_iterations", "N/A")}')
		logger.info(f'Session stats - Questions generated: {state.get("total_questions_generated", 0)}, Completeness: {state.get("completeness_score", 0.0):.3f}')

		return state

	async def search_question_sessions(self) -> List[Dict[str, Any]]:
		"""
		Search question sessions with filtering.
		"""
		logger.info('Starting question sessions search')
		logger.info('MemorySaver does not support listing all sessions by default; you may need to extend it if needed')
		return []

	def get_service_info(self) -> Dict[str, Any]:
		"""Get repository and workflow information"""
		logger.info('Retrieving service information')

		try:
			workflow_info = self.workflow.get_workflow_info()
			config_dict = self.config.to_dict()

			service_info = {'name': 'Question Composer Repository', 'version': '1.0.0', 'workflow_info': workflow_info, 'config': config_dict, 'features': ['Intelligent question generation', 'User profile analysis', 'Session management', 'Adaptive questioning based on completeness', '4 question types support', 'Vietnamese language optimized', 'LangGraph workflow integration', 'Database persistence']}

			logger.info('Service information retrieved successfully')
			logger.info(f'Config keys: {list(config_dict.keys())}')
			logger.info(f'Workflow info keys: {list(workflow_info.keys())}')

			return service_info

		except Exception as e:
			logger.error(f'Error retrieving service info: {str(e)}', exc_info=True)
			return {'name': 'Question Composer Repository', 'version': '1.0.0', 'error': f'Failed to retrieve full info: {str(e)}'}
