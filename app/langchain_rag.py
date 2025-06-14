import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain


load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PGVector(
    connection_string=os.getenv("DATABASE_URL"),
    embedding_function=embedding,
    collection_name="plan_vector",
)

llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

multi_turn_template = """
당신은 통신 요금제 전문가입니다. 아래는 사용자와 나눈 최근 대화 기록입니다.

[이전 대화]
{chat_history}

[질문]
{question}

아래 요금제 설명에 적힌 요금제들 그대로 반환해주세요

[요금제 설명]
{context}
"""

multi_turn_prompt = PromptTemplate(
    input_variables=["chat_history", "context", "question"],
    template=multi_turn_template
)


def build_multi_turn_chain(chat_history: list[tuple[str, str]]):

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": multi_turn_prompt}
    )