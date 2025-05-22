from fastapi import APIRouter, Depends, Request, status
from typing import List, Dict, Any  # Added Dict, Any

from app.core.base_model import APIResponse
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions  # Using the decorator


from app.middleware.translation_manager import _
from app.modules.question_composer.repositories.question_agent_repo import (
	QuestionAgentRepository,
)
from app.modules.question_composer.schemas.question_agent_schema import (
	GeneratedQuestion,
	UserCharacteristicsInput,  # This is the input model for the request body
	QuestionCompositionAPIResponse,  # Outer API response structure
)

route = APIRouter(prefix='/question-composer', tags=['Question Agent'])


@route.post(
	'/compose-questions',
	response_model=APIResponse,  # Use the outer response model
	status_code=status.HTTP_200_OK,
)
@handle_exceptions  # Apply the decorator for exception handling
async def compose_questions_endpoint(
	request: Request,  # Keep request for potential lang or user context
	user_input: UserCharacteristicsInput,  # This expects {"characteristics": {"key": "value", ...}}
):
    """
    API endpoint to generate critical questions based on user characteristics.

    The process involves:
    1. Receiving unstructured JSON data about the user (wrapped in UserCharacteristicsInput).
    2. Querying a Knowledge Base (via RAG system) for relevant context.
    3. Generating an initial set of questions.
    4. Entering a self-reflection loop to evaluate and refine these questions.
    5. Selecting the top N critical questions to return to the user.
    """
    print(f'Received request to /compose-questions with input characteristics: {user_input}')

    repo = QuestionAgentRepository()
    composed_questions_result: List[GeneratedQuestion] = await repo.compose_questions(user_characteristics=user_input)

    print(f'Successfully composed questions in endpoint: {composed_questions_result}')

    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,  # Use .value for enums
        message=_('questions_composed_successfully'),
        data=composed_questions_result,
    )
