# app/dependencies/llm.py
from langchain_openai import ChatOpenAI

llm = None

def init_llm():
    global llm
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.7,
        streaming=True
    )

def get_llm():
    if llm is None:
        raise ValueError("LLM not initialized")
    return llm