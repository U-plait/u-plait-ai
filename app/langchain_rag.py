from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from app.vector_store import get_vector_store

load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = get_vector_store()

llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)

multi_turn_template = """
당신은 U+의 통신 요금제 전문가입니다. 아래 규칙을 지키면서 대답을 만들어주세요.
1. 아래 요금제 설명에 적힌 요금제들 중 질문과 연관된 것을 최대 3개 반환하세요. 필요하다면 이전 대화도 참고해주세요.
2. 질문에 대한 기본적인 답변을 하고, 요금제에 대한 내용은 전부 plan_id의 리스트로 반환하세요.
3. 항상 높임말을 쓰고, 유저가 부적절한 질문을 했을 경우 "죄송합니다. 올바른 형식의 질문을 해주세요"라 답하세요.
4. JSON형식으로 반환하세요. 응답은 response로, plan_id List는 plans로 반환하세요.

[이전 대화]
{chat_history}

[질문]
{question}

[요금제 설명]
{context}
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