import openai
from ..schemas.question import CandidateInput, GeneratedQuestion
from typing import List, Dict, Any

# Set your OpenAI API key
openai.api_key = 'your-api-key'

def generate_questions(candidate: CandidateInput, survey: Dict[str, Any]) -> List[GeneratedQuestion]:
    # Construct the prompt for the LLM
    prompt = f"""
    Candidate Name: {candidate.name}
    Skills: {', '.join(candidate.skills)}
    Mindset: {', '.join(candidate.mindset)}
    CV Text: {candidate.cv_text}
    Survey Data: {survey}
    Generate specific questions to explore more about this candidate's abilities, skills, and mindset based on the survey data.
    """

    # Call the OpenAI API
    response = openai.Completion.create(
        engine="gpt-4o-mini", 
        prompt=prompt,
        max_tokens=1000,
        temperature=0.7,
        stop=None
    )

    # Extract questions from the response
    questions_text = response.choices[0].text.strip().split('\n')
    questions = [GeneratedQuestion(question_text=q, category="llm") for q in questions_text if q]

    return questions 