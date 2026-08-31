"""
U-Plait AI 서비스의 도메인 커스텀 지표 정의.

지표 이름 규약:
- 접두사 `chatbot_` (챗봇 파이프라인 관련), `uplait_ai_` (그 외 서비스 관련)
- Prometheus는 dot 대신 underscore를 사용하므로 여기서도 underscore로 통일
- 태그값은 영어 소문자 snake_case (Prometheus 쿼리 리터럴로 재사용)

이 파일은 모듈 로드 시 지표를 등록만 하고, 실제 값 증가는 각 라우터/서비스에서 수행.
"""

from __future__ import annotations

import os
from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# LLM 비용 / 성능
# ---------------------------------------------------------------------------

LLM_TOKENS = Counter(
    "chatbot_llm_tokens_total",
    "LLM 호출 시 사용된 토큰 수 (누적)",
    labelnames=("type", "model"),  # type=prompt|completion, model=gpt-4o-mini 등
)

LLM_COST_USD = Counter(
    "chatbot_llm_cost_usd_total",
    "LLM 사용에 발생한 예상 비용 (USD, 누적)",
    labelnames=("model",),
)

LLM_TTFT = Histogram(
    "chatbot_llm_ttft_seconds",
    "LLM 스트리밍 응답의 Time-To-First-Token (첫 청크가 사용자에게 도달할 때까지)",
    labelnames=("model",),
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0, float("inf")),
)

LLM_TOTAL_LATENCY = Histogram(
    "chatbot_llm_total_latency_seconds",
    "LLM 응답 완료까지의 종단 지연 (스트리밍 종료 시점까지)",
    labelnames=("model",),
    buckets=(0.5, 1, 2, 3, 5, 8, 13, 21, 34, 55, float("inf")),
)

LLM_RATE_LIMIT = Counter(
    "chatbot_llm_rate_limit_total",
    "LLM 프로바이더가 429 rate limit을 반환한 횟수",
    labelnames=("provider", "model"),
)

LLM_ERRORS = Counter(
    "chatbot_llm_errors_total",
    "LLM 호출 실패 (rate_limit 제외한 모든 오류)",
    labelnames=("provider", "model", "reason"),
)

# ---------------------------------------------------------------------------
# RAG 검색 품질
# ---------------------------------------------------------------------------

RETRIEVAL_LATENCY = Histogram(
    "chatbot_retrieval_latency_seconds",
    "pgvector 유사도 검색 지연",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, float("inf")),
)

RETRIEVAL_HITS = Histogram(
    "chatbot_retrieval_hits",
    "top-K 검색에서 실제 반환된 문서 수",
    buckets=(0, 1, 2, 3, 4, 5, 10, float("inf")),
)

RETRIEVAL_TOP1_SCORE = Histogram(
    "chatbot_retrieval_top1_score",
    "top-1 문서의 유사도 점수 (낮을수록 유사, pgvector cosine distance 기준)",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, float("inf")),
)

RETRIEVAL_EMPTY = Counter(
    "chatbot_retrieval_empty_total",
    "검색 결과가 하나도 없었던 요청 수 (RAG 실효성 저하 신호)",
)

# ---------------------------------------------------------------------------
# 추천 결과 (비즈니스 KPI)
# ---------------------------------------------------------------------------

RECOMMENDATION_RETURNED = Counter(
    "chatbot_recommendation_returned_total",
    "챗봇 응답이 반환한 요금제 추천 개수 버킷별 카운트",
    labelnames=("count_bucket",),  # 0 / 1 / 2 / 3+
)

RECOMMENDATION_FALLBACK = Counter(
    "chatbot_recommendation_fallback_total",
    "챗봇이 '알지 못하는 질문입니다' 등 폴백으로 응답한 횟수",
    labelnames=("source",),  # banword_input / banword_output / empty_plan_ids / parse_failure
)

SESSION_TURNS = Histogram(
    "chatbot_session_turns",
    "요청 시점 기준 최근 세션의 대화 턴 수 (history_pairs 개수)",
    buckets=(0, 1, 2, 3, 5, 8, 13, 21, float("inf")),
)

# ---------------------------------------------------------------------------
# 안전 / 가드레일
# ---------------------------------------------------------------------------

BANWORD_HIT = Counter(
    "chatbot_banword_hit_total",
    "금칙어 필터 적중 카운터",
    labelnames=("source",),  # input=사용자 질문 / output=LLM 응답 (더 위험)
)

# ---------------------------------------------------------------------------
# 요금제 인덱싱 (벡터 저장)
# ---------------------------------------------------------------------------

INDEXING_LATENCY = Histogram(
    "uplait_ai_plan_indexing_latency_seconds",
    "요금제 벡터 인덱싱 (임베딩 + DB 저장) 소요시간",
    labelnames=("result",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf")),
)

INDEXING_DESCRIPTION_CHARS = Histogram(
    "uplait_ai_plan_indexing_description_chars",
    "인덱싱된 요금제 description 문자 수 분포 (RAG 품질 예측 지표)",
    buckets=(50, 100, 200, 400, 800, 1600, 3200, float("inf")),
)

INDEXING_FAILURES = Counter(
    "uplait_ai_plan_indexing_failures_total",
    "인덱싱 실패를 사유별로 세분화한 카운터",
    labelnames=("reason",),  # embedding_error / db_error / unknown
)

INDEXING_TRIGGER = Counter(
    "uplait_ai_plan_indexing_trigger_total",
    "인덱싱을 트리거한 소스별 카운터 (Spring이 헤더로 전달)",
    labelnames=("trigger",),  # create / update / delete / unknown
)

# ---------------------------------------------------------------------------
# 유틸: 토큰 카운팅 + 비용 산정
# ---------------------------------------------------------------------------

# 가격은 env로 오버라이드 가능. 기본값은 gpt-4o-mini 참고가 (2024 기준).
# 실제 서비스 반영 시 config로 관리 권장.
_DEFAULT_MODEL = os.getenv("CHATBOT_LLM_MODEL", "gpt-4o-mini")
_INPUT_USD_PER_1K = float(os.getenv("CHATBOT_LLM_INPUT_USD_PER_1K", "0.00015"))
_OUTPUT_USD_PER_1K = float(os.getenv("CHATBOT_LLM_OUTPUT_USD_PER_1K", "0.00060"))

try:
    import tiktoken

    _enc_cache: dict[str, "tiktoken.Encoding"] = {}

    def _encoder(model: str) -> "tiktoken.Encoding":
        if model not in _enc_cache:
            try:
                _enc_cache[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                _enc_cache[model] = tiktoken.get_encoding("cl100k_base")
        return _enc_cache[model]

    def count_tokens(text: str, model: str = _DEFAULT_MODEL) -> int:
        if not text:
            return 0
        try:
            return len(_encoder(model).encode(text))
        except Exception:
            return max(1, len(text) // 4)  # 대략치 폴백
except ImportError:  # tiktoken 미설치 환경에서도 앱은 뜨도록 폴백
    def count_tokens(text: str, model: str = _DEFAULT_MODEL) -> int:
        return 0 if not text else max(1, len(text) // 4)


def record_llm_usage(prompt_text: str, completion_text: str, model: str | None = None) -> None:
    """LLM 요청/응답 텍스트로부터 토큰 수와 예상 비용을 지표에 기록."""
    m = model or _DEFAULT_MODEL
    prompt_tokens = count_tokens(prompt_text, m)
    completion_tokens = count_tokens(completion_text, m)
    if prompt_tokens:
        LLM_TOKENS.labels(type="prompt", model=m).inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(type="completion", model=m).inc(completion_tokens)
    cost = (prompt_tokens * _INPUT_USD_PER_1K + completion_tokens * _OUTPUT_USD_PER_1K) / 1000.0
    if cost > 0:
        LLM_COST_USD.labels(model=m).inc(cost)


def bucket_of(count: int) -> str:
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    return "3+"
