from typing import Any, Dict, List

from app.exceptions.exception import (
    CustomHTTPException,
    KnowledgeBaseConnectionException,
    QuestionGenerationException,
    SelfReflectionException,
)
from app.middleware.translation_manager import _
# from app.modules.agentic_rag.agent.rag_graph import મુખ્ય_graph as rag_graph  # Assuming this is your RAG graph
from app.modules.question_composer.schemas.question_agent_schema import (
    GeneratedQuestion,
    UserCharacteristicsInput,
)

# Placeholder for actual RAG graph interaction
# This would involve invoking the rag_graph with appropriate inputs
async def query_rag_system(query: str) -> Dict[str, Any]:
    """
    Placeholder function to simulate querying the RAG system.
    In a real implementation, this would interact with your RAG graph.
    """
    print(f"Querying RAG system with: {query}")
    # Simulate RAG output
    # Replace with actual rag_graph.invoke(...) call
    # rag_response = await rag_graph.ainvoke({"keys": {"input": query, "iterations": 5}})
    # print(f"RAG Response: {rag_response}")
    # return rag_response.get("generation", "No specific knowledge found.")
    if "domain" in query.lower():
        return {"knowledge": "Domain-specific knowledge: Software Engineering best practices."}
    elif "career" in query.lower():
        return {"knowledge": "Career patterns: Transitioning from junior to senior roles."}
    elif "industry" in query.lower():
        return {"knowledge": "Industry trends: Growing demand for AI specialists."}
    return {"knowledge": "General knowledge related to the query."}

class QuestionAgentRepository:
    """
    Repository for handling the logic of the question composer agent.
    """

    async def generate_initial_questions(
        self, user_characteristics: UserCharacteristicsInput, knowledge_context: Dict[str, Any]
    ) -> List[GeneratedQuestion]:
        """
        Generates an initial set of questions based on user characteristics and RAG knowledge.
        """
        print(f"Generating initial questions for user_characteristics: {user_characteristics.data}")
        print(f"Knowledge context for generation: {knowledge_context}")

        questions: List[GeneratedQuestion] = []
        q_id_counter: int = 1

        for key, value in user_characteristics.data.items():
            questions.append(
                GeneratedQuestion(
                    id=f"char_{q_id_counter}",
                    text=f"Based on your characteristic '{key}': {value}, how does this impact your career goals?",
                    category="characteristic_based"
                )
            )
            q_id_counter += 1

        if knowledge_context.get("knowledge"):
            questions.append(
                GeneratedQuestion(
                    id=f"kb_{q_id_counter}",
                    text=f"Considering the information: '{knowledge_context['knowledge']}', what are your thoughts?",
                    category="knowledge_based"
                )
            )
        
        if not questions:
            questions.append(
                GeneratedQuestion(
                    id="fallback_1",
                    text="What are your primary career aspirations at this moment?",
                    category="general_aspiration"
                )
            )

        print(f"Generated initial questions: {questions}")
        return questions

    async def evaluate_and_refine_questions(
        self, questions: List[GeneratedQuestion], user_characteristics: UserCharacteristicsInput, knowledge_context: Dict[str, Any]
    ) -> List[GeneratedQuestion]:
        """
        Evaluates and refines questions in a self-reflection loop.
        """
        print(f"Starting self-reflection for {len(questions)} questions.")
        refined_questions: List[GeneratedQuestion] = []

        for i, q in enumerate(questions):
            print(f"Reflecting on question {i+1}: {q.text}")
            refined_text: str = q.text
            if "impact" in q.text.lower() and "goals" in q.text.lower():
                refined_text = q.text.replace("how does this impact your career goals?", "can you elaborate on how this specific characteristic might shape your long-term career trajectory and decision-making?")
            elif "thoughts" in q.text.lower():
                refined_text = q.text.replace("what are your thoughts?", "how might this information influence your approach to career development or skill acquisition?")
            
            if knowledge_context.get("knowledge") and "software engineering" in knowledge_context["knowledge"].lower() and "software" not in refined_text.lower():
                refined_text += " Specifically, in the context of software engineering?"

            refined_questions.append(
                GeneratedQuestion(
                    id=f"{q.id}_refined",
                    text=refined_text,
                    category=q.category
                )
            )
        
        print(f"Refined questions: {refined_questions}")
        if not refined_questions and questions:
            print("Refinement resulted in empty list, returning original questions.")
            return questions
        return refined_questions

    async def select_critical_questions(
        self, questions: List[GeneratedQuestion], count: int = 10
    ) -> List[GeneratedQuestion]:
        """
        Selects the top N critical questions.
        """
        print(f"Selecting {count} critical questions from {len(questions)} questions.")
        selected_questions: List[GeneratedQuestion] = questions[:count]
        print(f"Selected questions: {selected_questions}")
        return selected_questions

    async def compose_questions(
        self, user_characteristics: UserCharacteristicsInput
    ) -> List[GeneratedQuestion]:
        """
        Main method to compose questions through the self-reflection module.
        """
        print(f"Starting question composition for user: {user_characteristics.data}")

        try:
            derived_query: str = "general career advice and domain knowledge related to " + ", ".join(user_characteristics.data.keys())
            knowledge_context: Dict[str, Any] = await query_rag_system(derived_query)
            print(f"Retrieved knowledge context: {knowledge_context}")
            if not knowledge_context or not knowledge_context.get("knowledge"):
                print("Warning: Knowledge base query returned no significant information.")

        except Exception as e:
            print(f"Error querying RAG system: {e}")
            raise KnowledgeBaseConnectionException(message=_('error_connecting_knowledge_base'))

        try:
            initial_questions: List[GeneratedQuestion] = await self.generate_initial_questions(
                user_characteristics, knowledge_context
            )
            if not initial_questions:
                print("No initial questions generated.")
                raise QuestionGenerationException(message=_('error_generating_initial_questions'))

            refined_questions: List[GeneratedQuestion] = initial_questions
            for i in range(2): # Simulate a few refinement iterations
                print(f"Self-reflection iteration {i+1}")
                current_refined_questions = await self.evaluate_and_refine_questions(
                    refined_questions, user_characteristics, knowledge_context
                )
                if not current_refined_questions and refined_questions: # check if refinement made it empty
                    print(f"Questions list became empty during refinement iteration {i+1}. Using previous list.")
                    # refined_questions remains as is from previous iteration
                    break
                refined_questions = current_refined_questions
            
            if not refined_questions:
                 print("No questions after refinement process.")
                 raise SelfReflectionException(message=_('error_in_self_reflection_resulted_empty'))

            final_questions: List[GeneratedQuestion] = await self.select_critical_questions(
                refined_questions, count=10
            )
            if not final_questions:
                print("No final questions selected.")
                raise QuestionGenerationException(message=_('error_no_questions_selected'))

            print(f"Successfully composed questions: {final_questions}")
            return final_questions

        except CustomHTTPException as e:
            print(f"CustomHTTPException during question composition: {e.message}")
            raise
        except Exception as e:
            print(f"Unexpected error during question composition: {e}")
            raise QuestionGenerationException(message=_('error_unexpected_question_generation'))
