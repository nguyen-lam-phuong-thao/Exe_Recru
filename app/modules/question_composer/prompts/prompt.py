"""
Prompts for the Question Composer Agent.
"""

# Prompt to generate a concise query for the RAG system based on user characteristics
PREPARE_KNOWLEDGE_QUERY_PROMPT = """
Based on the following user characteristics, generate a concise search query to find relevant knowledge 
for generating insightful interview questions. Focus on extracting key terms related to their role, 
experience, skills, and career aspirations.

User Characteristics:
{user_characteristics}

Search Query:
"""

# Prompt to generate initial questions based on user characteristics and retrieved knowledge
GENERATE_INITIAL_QUESTIONS_PROMPT = """
You are an expert career coach and interviewer. Based on the provided user characteristics and the 
retrieved knowledge context, generate a diverse set of {num_questions_to_generate} insightful and critical questions 
that would help understand the user's capabilities, experiences, and alignment with their career goals.

User Characteristics:
{user_characteristics}

Retrieved Knowledge Context:
{knowledge_context}

Generated Questions (provide as a numbered list of strings, ensure each question is a single string):
"""

# Prompt to critique generated questions
CRITIQUE_QUESTIONS_PROMPT = """
You are an expert evaluator of interview questions. Review the following list of generated questions, 
keeping in mind the user's characteristics and the knowledge context they were based on.
For each question, assess its:
1. Relevance: Is it directly relevant to the user's profile and context?
2. Clarity: Is the question clear and unambiguous?
3. Depth: Does it encourage a thoughtful and detailed response, or is it superficial?
4. Insightfulness: Does it have the potential to reveal significant insights about the candidate?
5. Uniqueness: Does it avoid being overly generic?

User Characteristics:
{user_characteristics}

Retrieved Knowledge Context:
{knowledge_context}

Generated Questions to Critique:
{generated_questions}

Critique (provide feedback for each question, and a summary of overall quality. Format as a single string of feedback.):
"""

# Prompt to refine questions based on critique
REFINE_QUESTIONS_PROMPT = """
You are an expert at refining interview questions. Based on the original questions, the user characteristics, 
the knowledge context, and the provided critique, please refine the questions. 
Your goal is to improve their relevance, clarity, depth, and insightfulness.
You can rephrase, combine, replace, or add new questions as needed to arrive at a stronger set of {num_questions_to_generate} questions.

User Characteristics:
{user_characteristics}

Retrieved Knowledge Context:
{knowledge_context}

Original Questions:
{generated_questions}

Critique:
{critique}

Refined Questions (provide as a numbered list of strings, ensure each question is a single string):
"""

# Prompt for the LLM to select the best N questions
SELECT_FINAL_QUESTIONS_PROMPT = """
From the following list of generated and refined questions, select the top {num_final_questions} most critical and insightful questions.
Consider relevance to the user's profile, potential impact, and overall diversity of the question set.

User Characteristics:
{user_characteristics}

Available Questions:
{generated_questions}

Selected Top {num_final_questions} Questions (provide as a numbered list of strings, ensure each question is a single string):
"""
