"""
U-Plait AI 서비스의 도메인 커스텀 지표 정의.

지표 이름 규약:
- 접두사 `chatbot_` (챗봇 파이프라인), `uplait_` (도메인 KPI), `uplait_ai_` (인프라 세부)
- Prometheus는 dot 대신 underscore를 사용
- 태그값은 영어 소문자 snake_case (Prometheus 쿼리 리터럴로 재사용)
- 절대 label로 넣지 않는 것: user_id, plan_id, recommendation_id, 원문 입력, 토큰 문자열, 예외 원문
"""

from __future__ import annotations

import os
from prometheus_client import Counter, Gauge, Histogram

# =============================================================================
# [P0] 추천 여정 SLI — U-Plait 서비스 수준 가용성의 최우선 지표
# =============================================================================

RECOMMENDATION_TOTAL = Counter(
    "uplait_recommendation_total",
    "추천 요청 결과. HTTP 200이어도 empty/invalid면 fail로 집계.",
    labelnames=("result", "stage", "failure_type"),
    # result: success|fail|empty|timeout|fallback
    # stage: retrieval|llm|validation|response  (fail 시 실패한 단계)
    # failure_type: none|upstream|parse|no_candidate|invalid_plan|unknown
)

RECOMMENDATION_DURATION = Histogram(
    "uplait_recommendation_duration_seconds",
    "추천 파이프라인 단계별 처리시간. total 은 사용자 체감 지연.",
    labelnames=("stage", "result"),
    # stage: input_processing|vector_search|llm_generation|validation|total
    # (embedding 은 pgvector.similarity_search 내부에서 발생 — vector_search 에 포함)
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 8, 13, 21, float("inf")),
)

RECOMMENDATION_INVALID = Counter(
    "uplait_recommendation_invalid_total",
    "추천 결과 검증에서 실패한 이유별 카운터 (조용한 장애 감지).",
    labelnames=("reason",),
    # missing_plan: 존재하지 않는 plan_id 추천
    # duplicate: 응답 내 plan_id 중복
    # constraint_mismatch: 사용자 조건과 충돌 (Phase later)
    # inactive_plan: 판매 종료 요금제 (Plan에 active 컬럼 생기면)
)

# =============================================================================
# [P0/P1] RAG 검색 품질 (result 라벨로 확장)
# =============================================================================

RETRIEVAL_TOTAL = Counter(
    "chatbot_retrieval_total",
    "RAG 검색 결과 분류.",
    labelnames=("result",),
    # hit: 요청한 K개 반환
    # insufficient: 1개 이상 but K보다 적음
    # empty: 0개
    # error: 예외
)

RETRIEVAL_LATENCY = Histogram(
    "chatbot_retrieval_latency_seconds",
    "pgvector 유사도 검색 지연 (embedding 포함).",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, float("inf")),
)

RETRIEVAL_HITS = Histogram(
    "chatbot_retrieval_hits",
    "top-K 검색에서 실제 반환된 문서 수 분포.",
    buckets=(0, 1, 2, 3, 4, 5, 10, float("inf")),
)

RETRIEVAL_TOP1_SCORE = Histogram(
    "chatbot_retrieval_top1_score",
    "top-1 문서의 유사도 점수 (pgvector distance, 낮을수록 유사).",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, float("inf")),
)

# =============================================================================
# [P1] Vector DB 정합성 — 조용한 장애 (요청마다 계산 X, 주기 잡이 세팅)
# =============================================================================

VECTOR_MISSING = Gauge(
    "uplait_vector_missing_count",
    "RDB의 plan 중 벡터가 없는 데이터 수 (주기 정합성 잡이 갱신).",
)

VECTOR_ORPHAN = Gauge(
    "uplait_vector_orphan_count",
    "원본 plan 이 없는데 벡터만 남은 데이터 수 (주기 정합성 잡이 갱신).",
)

VECTOR_SYNC_LAG = Gauge(
    "uplait_vector_sync_lag_seconds",
    "가장 최근 plan 수정 이후 정합성 검사가 재실행되기까지의 지연.",
)

VECTOR_SYNC_TOTAL = Counter(
    "uplait_vector_sync_total",
    "벡터 동기화 작업 결과 (HTTP 성공과 실제 동기화 성공 분리).",
    labelnames=("operation", "result"),
    # operation: create|update|delete|rebuild
    # result: success|error
)

# =============================================================================
# LLM 비용 / 성능  ([P1] result 라벨 추가로 실패 호출의 토큰 소비 분리)
# =============================================================================

LLM_TOKENS = Counter(
    "chatbot_llm_tokens_total",
    "LLM 호출 시 사용된 토큰 수 (누적). 실패 호출의 낭비 토큰도 분리 집계.",
    labelnames=("type", "model", "result"),
    # type: prompt|completion
    # result: success|error|timeout
)

LLM_COST_USD = Counter(
    "chatbot_llm_cost_usd_total",
    "LLM 사용에 발생한 예상 비용 (USD, 누적).",
    labelnames=("model", "result"),
)

LLM_TTFT = Histogram(
    "chatbot_llm_ttft_seconds",
    "LLM 스트리밍 응답의 Time-To-First-Token.",
    labelnames=("model",),
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 13.0, float("inf")),
)

LLM_TOTAL_LATENCY = Histogram(
    "chatbot_llm_total_latency_seconds",
    "LLM 응답 완료까지의 종단 지연 (스트리밍 종료 시점까지).",
    labelnames=("model",),
    buckets=(0.5, 1, 2, 3, 5, 8, 13, 21, 34, 55, float("inf")),
)

LLM_RATE_LIMIT = Counter(
    "chatbot_llm_rate_limit_total",
    "LLM 프로바이더 429 rate limit 카운터.",
    labelnames=("provider", "model"),
)

LLM_ERRORS = Counter(
    "chatbot_llm_errors_total",
    "LLM 호출 실패 (rate_limit 제외한 모든 오류).",
    labelnames=("provider", "model", "reason"),
)

# =============================================================================
# 추천 결과 부가 지표 (기존 유지)
# =============================================================================

RECOMMENDATION_RETURNED = Counter(
    "chatbot_recommendation_returned_total",
    "챗봇 응답이 반환한 요금제 추천 개수 버킷별 카운트.",
    labelnames=("count_bucket",),  # 0 / 1 / 2 / 3+
)

RECOMMENDATION_FALLBACK = Counter(
    "chatbot_recommendation_fallback_total",
    "챗봇이 폴백으로 응답한 횟수.",
    labelnames=("source",),
    # banword_input / banword_output / empty_plan_ids / parse_failure
)

SESSION_TURNS = Histogram(
    "chatbot_session_turns",
    "요청 시점 기준 최근 세션의 대화 턴 수.",
    buckets=(0, 1, 2, 3, 5, 8, 13, 21, float("inf")),
)

# =============================================================================
# 안전 / 가드레일
# =============================================================================

BANWORD_HIT = Counter(
    "chatbot_banword_hit_total",
    "금칙어 필터 적중 카운터.",
    labelnames=("source",),  # input | output
)

# =============================================================================
# 요금제 인덱싱 (기존 유지 — vector_sync_total 이 상위 개념으로 추가됨)
# =============================================================================

INDEXING_LATENCY = Histogram(
    "uplait_ai_plan_indexing_latency_seconds",
    "요금제 벡터 인덱싱 소요시간.",
    labelnames=("result",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf")),
)

INDEXING_DESCRIPTION_CHARS = Histogram(
    "uplait_ai_plan_indexing_description_chars",
    "인덱싱된 요금제 description 문자 수 분포.",
    buckets=(50, 100, 200, 400, 800, 1600, 3200, float("inf")),
)

INDEXING_FAILURES = Counter(
    "uplait_ai_plan_indexing_failures_total",
    "인덱싱 실패 사유별 카운터.",
    labelnames=("reason",),
)

INDEXING_TRIGGER = Counter(
    "uplait_ai_plan_indexing_trigger_total",
    "인덱싱 트리거 소스별 카운터 (Spring 헤더 기반).",
    labelnames=("trigger",),
)

# =============================================================================
# 유틸: 토큰 카운팅 + 비용 산정
# =============================================================================

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
            return max(1, len(text) // 4)
except ImportError:
    def count_tokens(text: str, model: str = _DEFAULT_MODEL) -> int:
        return 0 if not text else max(1, len(text) // 4)


def record_llm_usage(
    prompt_text: str,
    completion_text: str,
    model: str | None = None,
    result: str = "success",
) -> None:
    """LLM 요청/응답 텍스트로부터 토큰 수와 예상 비용을 result 라벨과 함께 기록."""
    m = model or _DEFAULT_MODEL
    prompt_tokens = count_tokens(prompt_text, m)
    completion_tokens = count_tokens(completion_text, m)
    if prompt_tokens:
        LLM_TOKENS.labels(type="prompt", model=m, result=result).inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(type="completion", model=m, result=result).inc(completion_tokens)
    cost = (prompt_tokens * _INPUT_USD_PER_1K + completion_tokens * _OUTPUT_USD_PER_1K) / 1000.0
    if cost > 0:
        LLM_COST_USD.labels(model=m, result=result).inc(cost)


def bucket_of(count: int) -> str:
    if count <= 0:
        return "0"
    if count == 1:
        return "1"
    if count == 2:
        return "2"
    return "3+"


def classify_retrieval(hits: int, k: int) -> str:
    """검색 결과 개수를 result 라벨로 분류."""
    if hits <= 0:
        return "empty"
    if hits < k:
        return "insufficient"
    return "hit"
