from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatTurnRequest, ChatResponse
from app.jwt_auth import get_current_user_id
from app.database import get_db
from app.models import ChatLog
from app.langchain_rag import build_multi_turn_chain
from langchain_community.vectorstores.pgvector import PGVector
import os
from langchain_openai import OpenAIEmbeddings


router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_turn(
    request: ChatTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # 이전 대화 불러오기
    history = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.sequence).all()
    history_pairs = []
    for i in range(0, len(history) -1, 2):
            question = history[i].log
            answer = history[i + 1].log
            history_pairs.append((question, answer))

    # ***** 이전 대화 출력 ***
    print("\n📚 [ 이전 대화 출력]")
    print(history_pairs)

    # *****로그 출력용*****
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = PGVector(
    connection_string=os.getenv("DATABASE_URL"),
    embedding_function=embedding,
    collection_name="plan_vector",
    )   
    # 1. 유사 문서 직접 검색 (출력용)
    docs = vectorstore.similarity_search(request.query, k=5)

    # 2. 로그 출력
    print("\n📚 [Retrieved Documents]")
    print(f"\n[DEBUG] Retrieved {len(docs)} documents.")
    for i, doc in enumerate(docs):
        print(f"Rank {i+1}: {doc.metadata.get('plan_id', 'N/A')} | {doc.page_content[:100]}", flush=True)
    docs_scores = vectorstore.similarity_search_with_score(request.query, k=5)
    print(f"\n[DEBUG] Retrieved {len(docs_scores)} documents.")
    for i, (doc, score) in enumerate(docs_scores):
        print(f"Rank {i+1}: Score={score:.3f} | {doc.page_content[:100]}")
    # *****로그 출력용*****

    # LangChain chain 생성
    chain = build_multi_turn_chain()
    answer = chain.run({
        "question": request.query,
        "chat_history": history_pairs
    })

    # 로그 저장: 질문 + 응답 2줄 저장
    user_seq = len(history) + 1
    bot_seq = user_seq + 1
    db.add(ChatLog(user_id=user_id, log=request.query, sequence=user_seq, is_chatbot=False))
    db.add(ChatLog(user_id=user_id, log=answer, sequence=bot_seq, is_chatbot=True))
    db.commit()

    return ChatResponse(answer=answer)