from typing import Dict, Any, List
from app.modules.question_composer.schemas.question import QuestionSet, Question, QuestionOption

class QuestionComposerAgent:
    def __init__(self):
        self.question_templates = {
            "career_goal": {
                "id": "career_goal",
                "title": "Career Goals",
                "questions": [
                    {
                        "id": "field",
                        "text": "What field are you currently targeting for your career development?",
                        "type": "single_choice",
                        "options": [
                            {"text": "Engineering & Technology", "value": "tech"},
                            {"text": "Business & Management", "value": "business"},
                            {"text": "Design & Creative", "value": "design"},
                            {"text": "Science & Research", "value": "science"},
                            {"text": "HR & Administration", "value": "hr"},
                            {"text": "Other", "value": "other"}
                        ]
                    },
                    {
                        "id": "position",
                        "text": "What specific position are you targeting in your chosen field?",
                        "type": "single_choice_or_text",
                        "options": [
                            {"text": "Backend Software Engineer", "value": "backend"},
                            {"text": "Frontend Software Engineer", "value": "frontend"},
                            {"text": "DevOps/Infrastructure Engineer", "value": "devops"},
                            {"text": "Data Analyst", "value": "data_analyst"},
                            {"text": "Other", "value": "other"}
                        ],
                        "depends_on": {"field": "tech"}
                    }
                ]
            },
            "experience": {
                "id": "experience",
                "title": "Professional Experience",
                "questions": [
                    {
                        "id": "years",
                        "text": "How many years of professional work experience do you have?",
                        "type": "single_choice",
                        "options": [
                            {"text": "No professional experience", "value": "0"},
                            {"text": "Less than 1 year", "value": "<1"},
                            {"text": "1-3 years", "value": "1-3"},
                            {"text": "3-5 years", "value": "3-5"},
                            {"text": "5+ years", "value": "5+"}
                        ]
                    }
                ]
            }
        }

    def compose_questions(self, context: Dict[str, Any]) -> List[QuestionSet]:
        """Compose questions based on the given context"""
        question_sets = []
        
        # Add career goal questions
        career_goal_set = self._create_question_set(self.question_templates["career_goal"])
        question_sets.append(career_goal_set)
        
        # Add experience questions
        experience_set = self._create_question_set(self.question_templates["experience"])
        question_sets.append(experience_set)
        
        return question_sets

    def _create_question_set(self, template: Dict[str, Any]) -> QuestionSet:
        """Create a question set from a template"""
        questions = []
        for q in template["questions"]:
            options = [QuestionOption(**opt) for opt in q.get("options", [])]
            question = Question(
                id=q["id"],
                text=q["text"],
                type=q["type"],
                options=options,
                depends_on=q.get("depends_on")
            )
            questions.append(question)
        
        return QuestionSet(
            id=template["id"],
            title=template["title"],
            questions=questions
        )

    def get_dependent_questions(self, question_set_id: str, answer: Dict[str, Any]) -> List[Question]:
        """Get questions that depend on the given answer"""
        question_set = self.question_templates.get(question_set_id)
        if not question_set:
            return []
            
        dependent_questions = []
        for q in question_set["questions"]:
            if q.get("depends_on"):
                matches = True
                for key, value in q["depends_on"].items():
                    if answer.get(key) != value:
                        matches = False
                        break
                if matches:
                    options = [QuestionOption(**opt) for opt in q.get("options", [])]
                    question = Question(
                        id=q["id"],
                        text=q["text"],
                        type=q["type"],
                        options=options,
                        depends_on=q.get("depends_on")
                    )
                    dependent_questions.append(question)
        
        return dependent_questions 