from langchain_google_genai import ChatGoogleGenerativeAI


def initialize_llm(api_key: str):
    return ChatGoogleGenerativeAI(
        model='gemini-1.5-flash',
        api_key=api_key,
        temperature=0.3,
        max_tokens=2024,
        request_timeout=30,
        max_retries=2,
        convert_system_message_to_human=True,
    ) 