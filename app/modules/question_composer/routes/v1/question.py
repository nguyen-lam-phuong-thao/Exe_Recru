from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.modules.question_composer.schemas.question import QuestionSet, QuestionComposerResponse
from app.modules.question_composer.agent.question_agent import QuestionComposerAgent

route = APIRouter(prefix='/question', tag=["Question"])
question_agent = QuestionComposerAgent()

@route.post("/compose", response_model=QuestionComposerResponse)
async def compose_questions(context: Dict[str, Any]):
    """
    Compose a set of questions based on the given context
    """
    try:
        question_sets = question_agent.compose_questions(context)
        return QuestionComposerResponse(question_sets=question_sets)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@route.get("/dependent/{question_set_id}", response_model=List[Question])
async def get_dependent_questions(question_set_id: str, answer: Dict[str, Any]):
    """
    Get questions that depend on the given answer
    """
    try:
        questions = question_agent.get_dependent_questions(question_set_id, answer)
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 