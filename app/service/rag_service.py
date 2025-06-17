# rag_service.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from app.core.vector_store import get_vector_store

load_dotenv()

vectorstore = get_vector_store()
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7, streaming=True)

multi_turn_template = """
당신은 U+의 통신 요금제 전문가입니다. 아래 규칙을 지켜서 답변하세요.
1. 아래 요금제 설명을 바탕으로 질문과 가장 관련 있는 요금제를 최대 3개까지 선택하세요필요하다면 이전 대화도 참고해주세요.
2. 기본적인 질문 응답을 먼저 message에 자연스럽게 설명한 뒤, 마지막에 [END_OF_MESSAGE]를 출력하세요.
3. 이후에 별도로 plan_ids를 아래 형식처럼 JSON으로 출력하세요.
3. 항상 높임말을 사용하고, 부적절한 질문일 경우 "죄송합니다. 올바른 형식의 질문을 해주세요."라고만 출력하세요.

[이전 대화]
{chat_history}

[질문]
{question}

[요금제 설명]
{context}


---

응답 예시:
[message]
이 요금제는 영상 콘텐츠를 자주 보시는 분께 적합합니다.
기본 데이터가 많고 추가 데이터도 자동 제공되어 만족도가 높습니다.
[END_OF_MESSAGE]
{{"plan_ids": [12, 25, 33]}}

지금부터 위 형식을 따라 출력하세요.
"""

multi_turn_prompt = PromptTemplate(
    input_variables=["chat_history", "context", "question"],
    template=multi_turn_template
)

def build_multi_turn_chain():
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": multi_turn_prompt}
    )