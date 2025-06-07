from typing import Dict, Any, List
from app.modules.question_composer.schemas.question import QuestionSet, Question, QuestionOption

class QuestionRepository:
    def __init__(self):
        self.question_sets: Dict[str, QuestionSet] = {}

    def create_question_set(self, question_set: QuestionSet) -> QuestionSet:
        """Create a new question set"""
        self.question_sets[question_set.id] = question_set
        return question_set

    def get_question_set(self, question_set_id: str) -> QuestionSet:
        """Get a question set by ID"""
        return self.question_sets.get(question_set_id)

    def update_question_set(self, question_set_id: str, question_set: QuestionSet) -> QuestionSet:
        """Update an existing question set"""
        if question_set_id in self.question_sets:
            self.question_sets[question_set_id] = question_set
            return question_set
        raise ValueError(f"Question set {question_set_id} not found")

    def delete_question_set(self, question_set_id: str) -> bool:
        """Delete a question set"""
        if question_set_id in self.question_sets:
            del self.question_sets[question_set_id]
            return True
        return False

    def list_question_sets(self) -> List[QuestionSet]:
        """List all question sets"""
        return list(self.question_sets.values())

    def get_questions_by_dependency(self, dependency_key: str, dependency_value: Any) -> List[Question]:
        """Get questions that depend on a specific condition"""
        dependent_questions = []
        for question_set in self.question_sets.values():
            for question in question_set.questions:
                if (question.depends_on and 
                    question.depends_on.get(dependency_key) == dependency_value):
                    dependent_questions.append(question)
        return dependent_questions 