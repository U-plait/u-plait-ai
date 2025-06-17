from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatTurnRequest
from app.core.jwt_auth import get_current_user_id
from app.core.database import get_db
from app.models.models import ChatLog
from app.service.rag_service import build_multi_turn_chain
from langchain_community.vectorstores.pgvector import PGVector
import os
import json
import asyncio
from langchain_openai import OpenAIEmbeddings
from fastapi.responses import StreamingResponse
from app.service.tag_service import update_user_tags


router = APIRouter()

@router.post("/chat")
async def chat_turn(
    request: ChatTurnRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # 이전 대화 불러오기
    history = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.created_at).all()
    history_pairs = []
    for i in range(0, len(history) -1, 2):
            question = history[i].log
            answer = history[i + 1].log
            history_pairs.append((question, answer))

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
    docs_scores = vectorstore.similarity_search_with_score(request.query, k=5)
    print(f"\n[DEBUG] Retrieved {len(docs_scores)} documents.")
    for i, (doc, score) in enumerate(docs_scores):
        print(f"Rank {i+1}: Score={score:.3f} | {doc.page_content[:100]}")
    # *****로그 출력용*****

    # LangChain chain 생성
    chain = build_multi_turn_chain()

    # 응답 스트리밍 함수
    async def gpt_stream():
         answer_buffer = ""  #GPT 답변
         plan_json_buffer = ""   # plan_ids
         is_plan_mode = False  # [END_OF_MESSAGE] 이후 plan_ids 존재 여부
    
         # LangChain chain을 비동기로 실행하면서 토큰 단위로 응답 수신
         async for chunk in chain.astream({
              "question": request.query,
              "chat_history": history_pairs
         }):

            # chunk가 dict이면 'answer' 필드에서 가져오고, 아니면 문자열로 처리
            token = chunk.get("answer", "") if isinstance(chunk, dict) else str(chunk)

            if "[END_OF_MESSAGE]" in token:
                is_plan_mode = True
                parts = token.split("[END_OF_MESSAGE]")

                # 메시지 부분만 스트리밍
                answer_buffer += parts[0]
                for char in parts[0]:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.01)

                yield f"data: [END_OF_MESSAGE]\n\n"

                # JSON이 같이 붙어온 경우 저장
                if len(parts) > 1:
                    plan_json_buffer += parts[1]
                    answer_buffer += "[END_OF_MESSAGE]" + parts[1]  # 🔥 여기를 추가
                continue

            # 이 시점의 token은 [END_OF_MESSAGE] 없는 일반 텍스트
            if not is_plan_mode:
                answer_buffer += token
                for char in token:
                    yield f"data: {char}\n\n"
                    await asyncio.sleep(0.01)
            else:
                plan_json_buffer += token

        # plan_ids 파싱
         try:
            plan_data = json.loads(plan_json_buffer.strip())
         except Exception:
            plan_data = {"plan_ids": []}

        # plan_ids JSON을 스트리밍 전송 (추후에 이거 기반으로 db에서 정보 가져오는 걸로 고쳐야함)
         yield f"data: {json.dumps(plan_data)}\n\n"

        # 🔥 유저 태그 업데이트 호출 추가
         if plan_data.get("plan_ids"):
            update_user_tags(user_id=user_id, plan_ids=plan_data["plan_ids"], db=db)

        # 대화 로그 DB에 저장 (질문 + 답변)
         seq = len(history)+1
         db.add(ChatLog(user_id=user_id, log=request.query, is_chatbot=False))
         db.add(ChatLog(user_id=user_id, log=answer_buffer, is_chatbot=True))
         db.commit()
    return StreamingResponse(gpt_stream(), media_type="text/event-stream")