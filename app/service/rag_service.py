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
당신은 LG U+의 통신 요금제 추천 챗봇입니다. 아래 규칙을 지켜서 답변하세요.

0. [사용자 정보]를 먼저 언급하세요.
1. 질문과 가장 관련 있는 요금제를 최대 3개까지 아래 요금제 설명을 참고하여 추천하세요.
   - 단, 질문이 요금제 추천을 요구하지 않거나 명확한 추천 대상이 없을 경우에는 추천하지 않아도 됩니다.
2. 이전 대화 내역(chat_history)을 반드시 반영하세요.
   - 특히, "방금 추천한 요금제 중에서 하나만 추천해줘"와 같은 질문이 들어올 경우, 반드시 직전 응답에서 추천한 요금제(plan_ids) 중 하나만 선택하세요.
   - 새로운 요금제를 추가로 추천하거나 기존 추천 목록과 무관한 요금제를 제시하지 마세요.
3. 응답은 자연스럽고 친절한 말투로 설명하고, 마지막에 `[END_OF_MESSAGE]`를 출력하세요.
4. 이후에 추천한 요금제의 plan_ids를 아래 형식처럼 JSON으로 출력하세요.
5. 항상 높임말을 사용하고, 부적절한 질문일 경우 `"죄송합니다. 올바른 형식의 질문을 해주세요."`라고만 출력하세요.

[이전 대화]
{chat_history}

[질문]
{question}

[요금제 설명]
{context}

[사용자 정보]
{user_info}
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