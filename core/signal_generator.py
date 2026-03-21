"""
core/signal_generator.py — 전략별 entry_fn → 크로스 감지 → 신호 생성 (v5.4)

[v5.4] 4시간봉 전략 추가 지원
  - 5m/15m/1h/4h 4종 혼합 운용
  - 5m=매 루프, 15m=3번째 루프, 1h=12번째 루프, 4h=48번째 루프마다 평가
  - pre-fetch: BTC/USDT 5m + 15m + 1h + 4h 네 캐시 워밍
  - 총 40개 전략 (5m×10 + 15m×10 + 1h×10 + 4h×10)

[v5.3] 1시간봉 전략 추가 지원
[v5.2] 5분봉 전략 추가 지원
[v5.0] WFA 전략 entry_fn 아키텍처로 전면 교체
"""

import pandas as pd
from datetime import datetime, timezone
from config import ALL_STRATEGIES
from strategies.registry import STRATEGY_REGISTRY
from strategies.indicators import ENTRY_FN_MAP, get_atr_value
from core.data_manager import fetch_ohlcv, fetch_ohlcv_parallel
from utils.logger import get_logger

logger = get_logger("signal_generator")

# ── 전략 공통 최소 필요 봉 수 ─────────────────────────────────────
# 이치모쿠(52) + EMA(50) + STDDEV EMA(20+20) + 여유 = 65봉
MIN_BARS_REQUIRED = 65


def _check_cross(entry_fn, df_full: pd.DataFrame) -> bool:
    """
    [v5.0] 크로스(전환) 감지 — entry_fn 기반.

    entry_fn은 True(조건 충족) / False(미충족) 반환.

    동작:
      1. result_curr = entry_fn(df_full)          # 현재 봉까지 포함
      2. result_prev = entry_fn(df_full.iloc[:-1]) # 현재 봉 제외
      3. 비교:
         - curr == False  → 조건 미충족 → False
         - curr == True AND prev == False → 전환(새 신호) → True
         - curr == True AND prev == True  → 유지 중 → False (무시)

    Returns:
        True  — 전환 감지됨 (새 신호)
        False — 전환 없음
    """
    if len(df_full) < 3:
        return False

    try:
        result_curr = entry_fn(df_full)
    except Exception:
        return False

    if not result_curr:
        return False  # 현재 봉 조건 미충족

    try:
        result_prev = entry_fn(df_full.iloc[:-1].copy())
    except Exception:
        # 이전 봉 계산 실패 → 안전하게 "전환으로 간주"
        return True

    # 전환 판단: prev=False → curr=True 일 때만 신호
    if not result_prev:
        return True
    else:
        return False  # 유지 중 → 무시


# ── [v5.3] 타임프레임별 봉 마감 체크 ──────────────────────────
# 5m 루프 기준: 5m=매 루프, 15m=3번째 루프(15분 정각), 1h=12번째 루프(정시)
_TF_SECONDS = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400}


def _is_candle_boundary(timeframe: str, utc_now: datetime | None = None) -> bool:
    """
    [v5.3] 현재 UTC 시각이 해당 타임프레임의 봉 마감 직후인지 판단.
    5분봉 루프 기준:
      5m  → 항상 True (매 루프)
      15m → minute이 0, 15, 30, 45일 때만 True
      1h  → minute == 0 (정시, 12번째 루프마다)
      4h  → hour % 4 == 0 and minute == 0
    """
    if utc_now is None:
        utc_now = datetime.now(timezone.utc)

    minute = utc_now.minute
    hour   = utc_now.hour

    if timeframe == "5m":
        return True
    elif timeframe == "15m":
        return minute % 15 == 0
    elif timeframe == "1h":
        return minute == 0
    elif timeframe == "4h":
        return hour % 4 == 0 and minute == 0
    else:
        return True


def generate_all_signals() -> list[dict]:
    """
    config.ALL_STRATEGIES에 등록된 전략만 감시/매매. (v5.4)

    [v5.4 변경점]
      - 5m + 15m + 1h + 4h 4종 혼합 운용
      - 5m=매 루프, 15m=3루프마다, 1h=12루프마다, 4h=48루프마다
      - pre-fetch: BTC/USDT 5m + 15m + 1h + 4h 네 캐시 워밍
    """
    signals = []
    utc_now = datetime.now(timezone.utc)

    # ── config.ALL_STRATEGIES 기반 활성 전략 필터링 ────
    active_strategies = {}
    for sid in ALL_STRATEGIES:
        if sid in STRATEGY_REGISTRY:
            active_strategies[sid] = STRATEGY_REGISTRY[sid]
        else:
            logger.warning(f"[SIGNAL] ⚠️ ALL_STRATEGIES에 '{sid}' 있으나 REGISTRY에 미등록 → 무시")

    # ── 타임프레임별 봉 마감 필터링 ────────────────────
    eligible_strategies = {}
    skipped_tf_counts: dict[str, int] = {}
    for sid, strat in active_strategies.items():
        tf = strat["timeframe"]
        if _is_candle_boundary(tf, utc_now):
            eligible_strategies[sid] = strat
        else:
            skipped_tf_counts[tf] = skipped_tf_counts.get(tf, 0) + 1

    tf_time_str = utc_now.strftime("%H:%M")
    if skipped_tf_counts:
        skip_detail = ", ".join(f"{tf}:{cnt}개" for tf, cnt in sorted(skipped_tf_counts.items()))
        logger.info(
            f"[SIGNAL] [{tf_time_str} UTC] 활성 {len(eligible_strategies)}개 "
            f"(전체 {len(active_strategies)}개 중 봉 미마감 스킵: {skip_detail})"
        )
    else:
        logger.info(
            f"[SIGNAL] [{tf_time_str} UTC] 활성 전략: {len(eligible_strategies)}개 "
            f"(전체 {len(active_strategies)}개 — 모든 타임프레임 봉 마감)"
        )

    if not eligible_strategies:
        logger.info(f"[SIGNAL] [{tf_time_str} UTC] 이번 루프에 평가할 전략 없음")
        return signals

    # ── 병렬 pre-fetch: 유니크 심볼/타임프레임 조합 캐시 워밍 ──
    unique_pairs = list({
        (s["symbol"], s["timeframe"])
        for s in eligible_strategies.values()
    })
    import time as _time
    t0 = _time.time()
    fetch_ohlcv_parallel(unique_pairs, limit=100)
    logger.info(f"[SIGNAL] 병렬 pre-fetch {len(unique_pairs)}개 완료 ({_time.time()-t0:.2f}초)")

    for strategy_id, strategy in eligible_strategies.items():
        symbol    = strategy["symbol"]
        timeframe = strategy["timeframe"]
        direction = strategy["direction"]

        # OHLCV 데이터 fetch (캐시 히트)
        df = fetch_ohlcv(symbol, timeframe, limit=100)
        if df is None or len(df) < MIN_BARS_REQUIRED:
            logger.warning(
                f"[SIGNAL] {strategy_id} — 데이터 부족 "
                f"({len(df) if df is not None else 0}봉 < 필요 {MIN_BARS_REQUIRED}봉), 스킵"
            )
            continue

        # ── entry_fn 기반 크로스 감지 ──────────────
        entry_fn_name = strategy.get("entry_fn", "")
        entry_fn = ENTRY_FN_MAP.get(entry_fn_name)
        if entry_fn is None:
            logger.warning(f"[SIGNAL] {strategy_id} — entry_fn '{entry_fn_name}' 미정의 → 스킵")
            continue

        try:
            is_cross = _check_cross(entry_fn, df)
        except Exception as e:
            logger.error(f"[SIGNAL] {strategy_id} 크로스 체크 오류: {e}")
            continue

        if not is_cross:
            continue

        entry_price = float(df["close"].iloc[-1])
        atr         = get_atr_value(df)

        logger.info(
            f"[SIGNAL] ✅ {strategy_id} 크로스 신호 발생 | {direction.upper()} | "
            f"Score: {strategy.get('score', 0):.2f} | "
            f"진입가: {entry_price:.4f} | ATR: {atr:.4f}"
        )

        signals.append({
            "strategy":    strategy,
            "signal":      True,
            "direction":   direction,
            "entry_price": entry_price,
            "atr":         atr,
        })

    return signals
