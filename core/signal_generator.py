"""
core/signal_generator.py — 전략별 3개 지표 AND 조건 → 신호 생성
"""

import pandas as pd
from strategies.registry import STRATEGY_REGISTRY
from strategies.indicators import INDICATOR_MAP, get_atr_value
from core.data_manager import fetch_ohlcv, fetch_ohlcv_parallel
from utils.logger import get_logger

logger = get_logger("signal_generator")

# 지표별 최소 필요 봉 수 (ICHIMOKU가 가장 큼: senkou=52 + 26선행 = 78봉)
_INDICATOR_MIN_BARS = {
    "ICHIMOKU": 80,   # 78봉 + 여유 2봉
    "AROON":    28,
    "OBV":      22,
    "CMF":      22,
    "EMA":      22,
    "SMA":      22,
    "VWAP":     22,
    "ATR_SIG":  22,
    "ADX":      16,
    "RSI":      16,
    "MFI":      16,
    "WILLR":    16,
    "PSAR":     12,
    "ROC":      14,
    "MOM":      12,
}

def _min_bars_required(indicators: list) -> int:
    """전략의 지표 목록 기준 최소 필요 봉 수 반환"""
    return max(_INDICATOR_MIN_BARS.get(ind, 20) for ind in indicators)


def generate_all_signals() -> list[dict]:
    """
    13개 전략 전수 신호 계산.
    신호 발생 시 signal dict 반환, 미발생 시 리스트에서 제외.

    v2.5: 유니크 (symbol, timeframe) 조합 병렬 pre-fetch → 직렬 대기 제거
    """
    signals = []

    # ── 병렬 pre-fetch: 유니크 조합 먼저 캐시 워밍 ──────────
    unique_pairs = list({
        (s["symbol"], s["timeframe"])
        for s in STRATEGY_REGISTRY.values()
    })
    import time as _time
    t0 = _time.time()
    fetch_ohlcv_parallel(unique_pairs, limit=100)
    logger.info(f"[SIGNAL] 병렬 pre-fetch {len(unique_pairs)}개 완료 ({_time.time()-t0:.2f}초)")

    for strategy_id, strategy in STRATEGY_REGISTRY.items():
        symbol    = strategy["symbol"]
        timeframe = strategy["timeframe"]

        # OHLCV 데이터 fetch (캐시 히트)
        df = fetch_ohlcv(symbol, timeframe, limit=100)
        min_bars = _min_bars_required(strategy["indicators"])
        if df is None or len(df) < min_bars:
            logger.warning(
                f"[SIGNAL] {strategy_id} — 데이터 부족 "
                f"({len(df) if df is not None else 0}봉 < 필요 {min_bars}봉), 스킵"
            )
            continue

        # 3개 지표 AND 조건 체크
        indicators = strategy["indicators"]
        results = []
        for ind_name in indicators:
            fn = INDICATOR_MAP.get(ind_name)
            if fn is None:
                logger.warning(f"[SIGNAL] {strategy_id} — 지표 '{ind_name}' 미정의")
                results.append(False)
                continue
            try:
                result = fn(df)
                results.append(result)
            except Exception as e:
                logger.error(f"[SIGNAL] {strategy_id} {ind_name} 계산 오류: {e}")
                results.append(False)

        # 3개 모두 True여야 신호
        if not all(results):
            continue

        entry_price = float(df["close"].iloc[-1])
        atr         = get_atr_value(df)

        logger.info(f"[SIGNAL] ✅ {strategy_id} 신호 발생 | 진입가: {entry_price:.4f}")

        signals.append({
            "strategy":    strategy,
            "signal":      True,
            "entry_price": entry_price,
            "atr":         atr,
        })

    return signals
