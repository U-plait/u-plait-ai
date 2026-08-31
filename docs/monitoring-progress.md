# U-Plait AI 관측성(Observability) 작업 진행 상황

> ⚠️ **이 브랜치는 절대 `develop` / `main` 에 병합하지 마세요.**
> `feat/observability-setup` 자체가 이 관측성 작업의 사실상 main으로 계속 사용됩니다.
> 필요한 커밋은 이 브랜치에서 계속 쌓아 나가면 됩니다.

## 1. 이 브랜치의 목적

U-Plait 백엔드(u-plait-be)의 관측성 브랜치와 **한 세트**로 동작.
Spring 쪽은 액츄에이터+Micrometer로 요금제 인덱싱·인증·배치 등을 계측했고,
**챗봇의 진짜 심장(RAG 검색 · LLM 호출 · 토큰/비용 · 추천 품질)** 은 FastAPI 쪽에서만 관측 가능하기에
이 레포에도 동일 스택(Prometheus 노출)을 붙여 그림을 완성하는 것이 목적입니다.

## 2. 아키텍처

```
┌──────────────┐        ┌───────────────┐        ┌────────────┐
│  Spring BE   │──POST─▶│  FastAPI AI   │──sim──▶│  pgvector  │
│  (u-plait-be)│  hdr   │ (u-plait-ai)  │  LLM──▶│  + OpenAI  │
└──────┬───────┘        └───────┬───────┘        └────────────┘
       │ /actuator/prometheus       │ /metrics
       ▼                             ▼
       Prometheus (u-plait-be/monitoring/docker-compose.monitoring.yml) 가 양쪽 스크래핑
       Grafana 대시보드도 u-plait-be 레포에 있음
```

Prometheus 및 Grafana 스택 자체는 **u-plait-be 쪽 레포**에 정의되어 있음
(`docker-compose.monitoring.yml`, `monitoring/prometheus.yml`, `monitoring/grafana/...`).
이 레포는 **FastAPI 프로세스가 `/metrics` 엔드포인트를 노출**하는 것까지만 담당.

## 3. 이 브랜치에서 완료된 것

### 3.1 새 파일
```
app/observability/__init__.py
app/observability/metrics.py       # 도메인 커스텀 지표 전체 정의 + 토큰 카운팅/비용 유틸
```

### 3.2 코드 변경
| 파일 | 변경 내용 |
|---|---|
| `app/requirements.txt` | `prometheus-client==0.20.0`, `prometheus-fastapi-instrumentator==7.0.0`, `tiktoken==0.7.0` 추가 |
| `app/main.py` | `Instrumentator().instrument(app).expose(app, "/metrics")` 로 HTTP + custom 지표 노출 |
| `app/api/chat_router.py` | RAG 검색 지연/hits/top1_score/empty, 입력 금칙어 카운터, 세션 턴 수 히스토그램 |
| `app/api/vector_router.py` | 인덱싱 지연, description 길이, 실패 사유별(embedding_error/db_error) 카운터, `X-Uplait-Trigger` 헤더로 트리거 소스 태깅 |
| `app/service/stream_service.py` | TTFT · 총 LLM 지연 · 토큰/비용(tiktoken) · rate limit / 일반 에러 · 추천 개수 버킷 · 폴백 분류(parse_failure/empty_plan_ids/banword_output) · **출력 금칙어 검사** |

### 3.3 등록된 커스텀 지표 전체 목록

**LLM 비용 / 성능**
- `chatbot_llm_tokens_total{type=prompt|completion, model}` — 누적 토큰 사용량
- `chatbot_llm_cost_usd_total{model}` — 예상 비용 USD (env로 단가 오버라이드)
- `chatbot_llm_ttft_seconds{model}` — Time-To-First-Token 히스토그램
- `chatbot_llm_total_latency_seconds{model}` — 스트리밍 종단 지연 히스토그램
- `chatbot_llm_rate_limit_total{provider,model}` — 429 카운터
- `chatbot_llm_errors_total{provider,model,reason}` — 일반 에러 카운터

**RAG 검색 품질**
- `chatbot_retrieval_latency_seconds` — pgvector 유사도 검색 지연
- `chatbot_retrieval_hits` — 반환 문서 수 히스토그램
- `chatbot_retrieval_top1_score` — top-1 유사도 점수 (pgvector distance, 낮을수록 유사)
- `chatbot_retrieval_empty_total` — 아무것도 못 찾은 요청 카운터

**추천 결과 (KPI)**
- `chatbot_recommendation_returned_total{count_bucket=0|1|2|3+}`
- `chatbot_recommendation_fallback_total{source=banword_input|banword_output|empty_plan_ids|parse_failure}`
- `chatbot_session_turns` — 세션당 대화 턴 수 히스토그램

**안전 / 가드레일**
- `chatbot_banword_hit_total{source=input|output}` — output 급증 = 브랜드 리스크 신호

**요금제 인덱싱**
- `uplait_ai_plan_indexing_latency_seconds{result=success|error}`
- `uplait_ai_plan_indexing_description_chars` — description 길이 분포
- `uplait_ai_plan_indexing_failures_total{reason=embedding_error|db_error}`
- `uplait_ai_plan_indexing_trigger_total{trigger=create|update|delete|unknown}`

### 3.4 파생 KPI (Prometheus recording rule로 정의 예정 — 챕터 2)
- **대화당 비용**: `sum(rate(chatbot_llm_cost_usd_total[1h])) / sum(rate(http_requests_total{handler="/chat"}[1h]))`
- **RAG 유용도**: `1 - (rate(chatbot_retrieval_empty_total[5m]) / rate(chatbot_retrieval_latency_seconds_count[5m]))`
- **추천 성공률**: `sum(rate(chatbot_recommendation_returned_total{count_bucket!="0"}[5m])) / sum(rate(chatbot_recommendation_returned_total[5m]))`

## 4. LLM 비용 산정 방식

기본 단가는 gpt-4o-mini 기준 (2024 참고):
- Input:  $0.00015 / 1K tokens (env `CHATBOT_LLM_INPUT_USD_PER_1K`)
- Output: $0.00060 / 1K tokens (env `CHATBOT_LLM_OUTPUT_USD_PER_1K`)
- 모델명: env `CHATBOT_LLM_MODEL` (기본 `gpt-4o-mini`)

토큰 카운팅은 `tiktoken` 사용. 스트리밍 시 응답 토큰은 누적 버퍼(`answer_buffer`)를 재인코딩해 계산.
정확한 사용량 계측이 아니라 **비용 알림용 근사치**임 — OpenAI usage 필드가 아직 확실하지 않은 상황에서
"토큰이 몇 배로 튀었냐"를 감지하는 용도로 충분함.

## 5. 로컬 실행 방법

### 5.1 사전 조건
- Python 3.10+ 및 이 레포의 기존 `.env` (DATABASE_URL, OPENAI_API_KEY 등)
- u-plait-be 쪽 모니터링 스택이 이미 떠 있어야 지표를 볼 수 있음
  (`docker compose -f docker-compose.monitoring.yml up -d` in u-plait-be repo)

### 5.2 의존성 설치
```bash
pip install -r app/requirements.txt
```

### 5.3 FastAPI 기동
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.4 지표 확인
```bash
curl http://localhost:8000/metrics | grep -E "^chatbot_|^uplait_ai_"
```

### 5.5 Prometheus 타겟 등록 (u-plait-be 쪽에서)
`u-plait-be/monitoring/prometheus.yml` 에 다음 job 추가되어 있음:
```yaml
  - job_name: 'fastapi-ai'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['host.docker.internal:8000']
        labels:
          service: u-plait-ai
          env: local
```

## 6. 다음 세션이 이어서 할 것 (챕터 2 준비)

1. **Grafana 커스텀 대시보드에 FastAPI 섹션 추가** (u-plait-be 레포)
   - 챗봇 파이프라인 P95 (TTFT, 전체지연)
   - 토큰 사용량 / 예상 비용 (누적)
   - RAG retrieval hit rate / top-1 점수 분포
   - 추천 결과 분포 / 폴백 사유별
   - 금칙어 in output 별도 강조 패널
2. **Prometheus alert rules** 초안 (`monitoring/rules/*.yml`, u-plait-be)
   - LLM 시간당 비용 임계치 초과 (예: $10/h)
   - retrieval empty ratio > 10% for 10m
   - banword_output 발생 (즉시 알림)
   - LLM rate_limit 발생
3. **Spring 쪽에서 `X-Uplait-Trigger` 헤더 전송** 하도록 `FastAPIClient.saveVector` 시그니처 확장 (u-plait-be)
4. **알림 콘솔** 신규 레포 시작 (Alertmanager webhook 수신, 이력 저장, React UI)

## 7. 알려진 이슈 / 주의사항

- **tiktoken이 최초 사용 시 인코딩 다운로드**: 오프라인 배포 시 미리 다운로드 필요
- **model_name 추출은 LangChain 내부 구조 의존** — 실패 시 `unknown` 라벨로 폴백 (지표는 정상 기록됨)
- **`X-Uplait-Trigger` 헤더 없으면 `unknown`** — Spring 쪽에서 아직 전송하지 않음
- **비용은 근사치**: 실제 청구는 OpenAI 대시보드가 원천. 지표는 "이상 감지" 용도
- **banword 출력 검사는 스트리밍 완료 후**에 수행 → 이미 사용자에게 도달한 뒤 감지. 실시간 차단이 필요하면 청크별 검사로 확장 필요
- **`X-Uplait-Trigger` 헤더 라벨 값**: `create|update|delete|unknown` 만 사용해서 카디널리티 폭발 방지

## 8. 참고

- prometheus-fastapi-instrumentator: https://github.com/trallnag/prometheus-fastapi-instrumentator
- tiktoken: https://github.com/openai/tiktoken
