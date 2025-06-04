from fastapi import APIRouter
from ..schemas.question import CandidateInput, GeneratedQuestion
from ..agent.generator import generate_questions
from typing import List

router = APIRouter()

@router.post("/generate", response_model=List[GeneratedQuestion])
def generate(candidate: CandidateInput):
    return generate_questions(candidate) 