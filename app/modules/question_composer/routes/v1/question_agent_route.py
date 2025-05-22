from fastapi import APIRouter, Depends, Request, status
from typing import List  # Added typing.List
from app.core.base_model import APIResponse
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.modules.question_composer.repositories.question_agent_repo import QuestionAgentRepository
from app.modules.question_composer.schemas.question_agent_schema import (
    UserCharacteristicsInput,
    QuestionCompositionAPIResponse,
    QuestionCompositionResponseData,
    GeneratedQuestion
)

route = APIRouter(prefix='/question-composer', tags=['Question Agent'])

@route.post("/compose-questions", response_model=QuestionCompositionAPIResponse, status_code=status.HTTP_200_OK)
@handle_exceptions
async def compose_questions_endpoint(
    request: Request,
    user_input: UserCharacteristicsInput,
    repo: QuestionAgentRepository = Depends(QuestionAgentRepository)
):
    """
    API endpoint to generate critical questions based on user characteristics.

    The process involves:
    1. Receiving unstructured JSON data about the user.
    2. Querying a Knowledge Base (via RAG system) for relevant context.
    3. Generating an initial set of questions.
    4. Entering a self-reflection loop to evaluate and refine these questions.
    5. Selecting the top N critical questions to return to the user.
    """
    print(f"Received request to /compose-questions with input: {user_input.data}")
    
    # The handle_exceptions decorator will manage exceptions raised from the repo
    generated_questions: List[GeneratedQuestion] = await repo.compose_questions(user_input)
    print(f"Successfully composed questions in endpoint: {generated_questions}")

    response_data = QuestionCompositionResponseData(questions=generated_questions)
    return QuestionCompositionAPIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("questions_composed_successfully"),
        data=response_data
    )

# Example of how you might add a knowledge base interaction route (conceptual)
# This would likely live in your agentic_rag module or a shared utility
# For now, this is just a placeholder to illustrate the concept based on the flowchart

# @route.post("/query-knowledge-base", status_code=status.HTTP_200_OK)
# @handle_exceptions
# async def query_knowledge_base_endpoint(request: Request, query: str):
#     """
#     (Conceptual) Endpoint to directly query the knowledge base.
#     This might be used for debugging or specific KB interactions.
#     """
#     print(f"Received request to /query-knowledge-base with query: {query}")
#     # In a real scenario, this would call a method in a RAG repository
#     # from app.modules.agentic_rag.repositories.rag_repo import RAGRepository (example)
#     # rag_repo = RAGRepository()
#     # knowledge_response = await rag_repo.query_knowledge(query)
#     knowledge_response = {"info": f"Knowledge related to '{query}' would be here."}
#     return APIResponse(
#         error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
#         message=_("knowledge_base_queried_successfully"),
#         data=knowledge_response
#     )
