"""
Vector DB 정합성 주기 검사 잡.

플랜 원본(RDB `plan`)과 벡터 저장소(`langchain_pg_embedding`)의 정합성을
주기적으로 스캔해 Gauge 지표를 갱신한다. 요청 경로에서 계산하지 않는다.

동작 조건:
- env `VECTOR_INTEGRITY_INTERVAL_SEC` (기본 300초). 0 이하이면 스케줄러 비활성.
"""

from __future__ import annotations

import logging
import os
import time
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.observability import metrics as m

log = logging.getLogger(__name__)

_INTERVAL = int(os.getenv("VECTOR_INTEGRITY_INTERVAL_SEC", "300"))

# 정합성 잡이 마지막으로 완료된 시각. `sync_lag_seconds` 계산에 사용.
_last_run_ts: float = 0.0


def _run_integrity_check_sync(db: Session) -> None:
    global _last_run_ts

    # missing: RDB의 plan 중 벡터가 없는 것
    missing = db.execute(text("""
        SELECT COUNT(*) FROM plan p
        WHERE NOT EXISTS (
            SELECT 1 FROM langchain_pg_embedding e
            WHERE (e.cmetadata->>'plan_id')::bigint = p.id
        )
    """)).scalar() or 0

    # orphan: 벡터는 있는데 원본 plan 이 없는 것
    orphan = db.execute(text("""
        SELECT COUNT(*) FROM langchain_pg_embedding e
        WHERE NOT EXISTS (
            SELECT 1 FROM plan p
            WHERE p.id = (e.cmetadata->>'plan_id')::bigint
        )
    """)).scalar() or 0

    m.VECTOR_MISSING.set(int(missing))
    m.VECTOR_ORPHAN.set(int(orphan))
    _last_run_ts = time.time()
    m.VECTOR_SYNC_LAG.set(0.0)  # 방금 잡이 완료했으므로 lag=0

    log.info("[vector_integrity] missing=%d orphan=%d", missing, orphan)


def run_once() -> None:
    """스케줄러가 호출하는 진입점. 세션은 매 실행마다 새로 열고 닫는다."""
    db = SessionLocal()
    try:
        _run_integrity_check_sync(db)
    except Exception as ex:  # noqa: BLE001 — 정합성 잡 실패가 앱을 죽여선 안 됨
        log.error("[vector_integrity] check failed: %s", ex, exc_info=True)
    finally:
        db.close()


def _tick_lag() -> None:
    """가장 최근 잡 완료 이후 경과 시간을 업데이트. 잡 자체 스케줄과 별개로 매 분 갱신."""
    if _last_run_ts:
        m.VECTOR_SYNC_LAG.set(time.time() - _last_run_ts)


def start_scheduler() -> None:
    """FastAPI startup 훅에서 호출. AsyncIOScheduler 로 백그라운드 실행."""
    if _INTERVAL <= 0:
        log.info("[vector_integrity] disabled (VECTOR_INTEGRITY_INTERVAL_SEC<=0)")
        return

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        log.warning("[vector_integrity] apscheduler 미설치 — 잡 비활성")
        return

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_once, "interval", seconds=_INTERVAL, id="vector-integrity")
    scheduler.add_job(_tick_lag, "interval", seconds=60, id="vector-integrity-lag")
    scheduler.start()
    log.info("[vector_integrity] scheduler started (interval=%ds)", _INTERVAL)
    # 시작 직후 한 번 즉시 실행해 초기 값 세팅
    run_once()
