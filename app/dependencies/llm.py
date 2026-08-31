"""
LLM 초기화. 기본은 ChatOpenAI(gpt-4o-mini) — 실제 서비스 흐름.
env USE_MOCK_LLM=true 인 경우 로컬 시연/부하 테스트용 MockChatModel 을 반환한다.
Mock 은 항상 동일 응답을 스트리밍하며, [END_OF_MESSAGE] + plan JSON 포맷을 지킨다.
"""

import os
from typing import Any, AsyncIterator, Iterator, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)

llm = None


class MockChatModel(BaseChatModel):
    """가짜 챗 모델. 항상 동일 응답을 청크로 흘려주어 지표 수집 흐름을 시연."""

    model_name: str = "mock-gpt-4o-mini"

    def _default_response(self) -> str:
        return (
            "안녕하세요. 문의 주신 조건에 맞춰 요금제를 추천드립니다. "
            "5G 스탠다드가 가장 적합해 보이며, 가족결합 시 추가 할인이 있습니다. "
            "[END_OF_MESSAGE]"
            "{\"plan_ids\": [1, 2, 3]}"
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = self._default_response()
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        text = self._default_response()
        for i in range(0, len(text), 8):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 8]))

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        text = self._default_response()
        for i in range(0, len(text), 8):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 8]))

    @property
    def _llm_type(self) -> str:
        return "mock-chat"


def init_llm():
    global llm
    if os.getenv("USE_MOCK_LLM", "").lower() in ("true", "1", "yes"):
        print("[LLM] USE_MOCK_LLM=true → MockChatModel 사용")
        llm = MockChatModel()
        return
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.7,
        streaming=True,
    )


def get_llm():
    if llm is None:
        raise ValueError("LLM not initialized")
    return llm
