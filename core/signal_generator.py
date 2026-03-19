"""
core/signal_generator.py — 전략별 지표 AND 조건 → 신호 생성 (v3.1)

[v3.1] config.py ALL_STRATEGIES 기반 전략 활성/비활성 필터 추가
  - signal_generator가 STRATEGY_REGISTRY 전체를 순회하는 대신
    config.ALL_STRATEGIES에 포함된 전략만 감시/매매
  - config.py를 수정하면 런타임에 전략 활성/비활성 제어 가능
  - STRATEGY_REGISTRY에 전략이 있어도 ALL_STRATEGIES에 없으면 무시

[v3.0] 백테스트 진입 타이밍 정확 재현 + direction 필터
  - v2.6 대비 핵심 변경:
    ① 크로스 감지: "조건 전환(False→True) 봉" 다음에만 신호 발생
       - 이전 봉(N-1) 신호 vs 현재 봉(N) 신호 비교
       - prev=False, curr=True  → 전환 = 신호 발생 ✅
       - prev=True,  curr=True  → 유지 중 = 무시 ❌
       - prev="short", curr="long" → 방향 전환 = 신호 발생 ✅
    ② direction 필터: strategy에 direction 필드 있으면 해당 방향만 허용
       - strategy["direction"]="short" → 지표가 "long" 반환해도 무시
    ③ _INDICATOR_MIN_BARS: 제거된 지표 삭제, 신규 지표 추가
  - 변경 근거: TASK.md 섹션 5 참조
"""

import pandas as pd
from config import ALL_STRATEGIES
from strategies.registry import STRATEGY_REGISTRY
from strategies.indicators import INDICATOR_MAP, get_atr_value
from core.data_manager import fetch_ohlcv, fetch_ohlcv_parallel
from utils.logger import get_logger

logger = get_logger("signal_generator")

# ── 지표별 최소 필요 봉 수 ─────────────────────────────────────
# [v3.0] 제거된 지표 삭제: ICHIMOKU, PSAR, RSI, WILLR, EMA, SMA
# [v3.0] 신규 지표 추가: AD, CCI, STDDEV
# 크로스 감지를 위해 df.iloc[:-1]도 사용하므로 +1봉 여유 반영
_INDICATOR_MIN_BARS = {
    # 핵심 거래량 지표
    "OBV":      25,    # SMA(20) + 여유
    "CMF":      25,    # period(20) + 여유
    "VWAP":     5,     # VWAP 자체는 단일 봉도 가능, 여유 확보
    "AD":       25,    # SMA(20) + 여유
    # 모멘텀
    "MOM":      15,    # period(10) + 여유
    "ROC":      15,    # period(10) + 여유
    # 보조
    "AROON":    30,    # period(25) + 여유
    "CCI":      25,    # period(20) + 여유
    "MFI":      20,    # period(14) + 여유
    "STDDEV":   35,    # period(20) + EMA(20) + 여유
    # 필터
    "ADX":      20,    # period(14) + 여유
    "ATR_SIG":  25,    # ATR(14) + SMA(20) + 여유
}


def _min_bars_required(indicators: list) -> int:
    """전략의 지표 목록 기준 최소 필요 봉 수 반환"""
    return max(_INDICATOR_MIN_BARS.get(ind, 25) for ind in indicators)


def _check_cross(fn, df_full: pd.DataFrame) -> str | bool:
    """
    [v3.0] 크로스(전환) 감지 — 백테스트 진입 타이밍 재현.

    개념:
      봇은 5분봉 마감 직후 실행. 이 시점에서:
      - df.iloc[-1] = 방금 확정된 봉 (현재 봉)
      - df.iloc[-2] = 그 직전 봉

      "현재 봉에서 조건이 완성"되려면:
        이전 봉까지는 조건 미충족 → 현재 봉에서 조건 충족

    동작:
      1. result_curr = fn(df_full)          # 현재 봉까지 포함
      2. result_prev = fn(df_full.iloc[:-1]) # 현재 봉 제외 (직전 봉까지)
      3. 비교:
         - curr == False         → 조건 미충족 → False
         - curr != False AND prev != curr → 전환(새 신호) → curr 반환
         - curr != False AND prev == curr → 유지 중 → False (무시)

    Args:
        fn: 지표 함수 (calc_obv, calc_adx 등)
        df_full: 전체 OHLCV DataFrame

    Returns:
        "long" / "short" — 전환 감지됨 (새 신호)
        False — 전환 없음 (조건 미충족 또는 유지 중)
    """
    # 최소 2봉 필요 (현재 + 이전)
    if len(df_full) < 3:
        return False

    try:
        result_curr = fn(df_full)
    except Exception:
        return False

    if not result_curr:
        return False  # 현재 봉 조건 미충족

    try:
        result_prev = fn(df_full.iloc[:-1].copy())
    except Exception:
        # 이전 봉 계산 실패 → 안전하게 "전환으로 간주"
        return result_curr

    # 전환 판단
    if result_prev != result_curr:
        # prev=False→curr="long"  또는  prev="short"→curr="long" 등
        # → 새로운 신호 (전환 발생)
        return result_curr
    else:
        # prev="long"→curr="long" 등 → 유지 중 → 무시
        return False


def generate_all_signals() -> list[dict]:
    """
    config.ALL_STRATEGIES에 등록된 전략만 감시/매매. (v3.1)

    [v3.1 변경점]
      - STRATEGY_REGISTRY 전체 대신 ALL_STRATEGIES에 포함된 전략만 순회
      - config.py에서 전략 추가/제거로 런타임 감시 범위 제어

    [v3.0 변경점]
      1. 크로스 감지: _check_cross()로 전환 시점만 신호 발생
      2. direction 필터: strategy["direction"]과 신호 방향 일치 확인
      3. 지표 AND 조건: 모든 지표가 같은 방향으로 "전환"되어야 함

    신호 발생 시 signal dict 반환, 미발생 시 리스트에서 제외.
    """
    signals = []

    # ── [v3.1] config.ALL_STRATEGIES 기반 활성 전략 필터링 ────
    active_strategies = {}
    for sid in ALL_STRATEGIES:
        if sid in STRATEGY_REGISTRY:
            active_strategies[sid] = STRATEGY_REGISTRY[sid]
        else:
            logger.warning(f"[SIGNAL] ⚠️ ALL_STRATEGIES에 '{sid}' 있으나 REGISTRY에 미등록 → 무시")

    logger.info(
        f"[SIGNAL] 활성 전략: {len(active_strategies)}개 "
        f"(REGISTRY {len(STRATEGY_REGISTRY)}개 중 ALL_STRATEGIES {len(ALL_STRATEGIES)}개 매칭)"
    )

    # ── 병렬 pre-fetch: 활성 전략의 유니크 조합만 캐시 워밍 ──
    unique_pairs = list({
        (s["symbol"], s["timeframe"])
        for s in active_strategies.values()
    })
    import time as _time
    t0 = _time.time()
    fetch_ohlcv_parallel(unique_pairs, limit=100)
    logger.info(f"[SIGNAL] 병렬 pre-fetch {len(unique_pairs)}개 완료 ({_time.time()-t0:.2f}초)")

    for strategy_id, strategy in active_strategies.items():
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

        # ── [v3.0] 크로스 감지 + 방향 일치 체크 ──────────────
        indicators = strategy["indicators"]
        required_direction = strategy.get("direction", "").lower()  # "long" or "short"

        cross_results = []
        for ind_name in indicators:
            fn = INDICATOR_MAP.get(ind_name)
            if fn is None:
                logger.warning(f"[SIGNAL] {strategy_id} — 지표 '{ind_name}' 미정의")
                cross_results.append(False)
                continue
            try:
                result = _check_cross(fn, df)
                cross_results.append(result)
            except Exception as e:
                logger.error(f"[SIGNAL] {strategy_id} {ind_name} 크로스 체크 오류: {e}")
                cross_results.append(False)

        # False(전환 없음) 제거 후 방향 집합 확인
        directions = [r for r in cross_results if r is not False and r]
        if not directions:
            continue  # 전환된 지표 없음

        unique_dirs = set(directions)
        if len(unique_dirs) != 1:
            # 지표들 사이 방향 불일치 → 스킵
            logger.debug(
                f"[SIGNAL] {strategy_id} 방향 불일치 {cross_results} → 스킵"
            )
            continue

        if len(directions) < len(indicators):
            # 일부 지표가 전환되지 않음 → AND 조건 미충족
            continue

        signal_direction = unique_dirs.pop()  # "long" or "short"

        # ── [v3.0] direction 필터: 전략 방향과 신호 방향 일치 확인 ──
        if required_direction and signal_direction != required_direction:
            logger.debug(
                f"[SIGNAL] {strategy_id} 방향 불일치 — "
                f"전략={required_direction}, 신호={signal_direction} → 스킵"
            )
            continue

        entry_price = float(df["close"].iloc[-1])
        atr         = get_atr_value(df)

        logger.info(
            f"[SIGNAL] ✅ {strategy_id} 크로스 신호 발생 | {signal_direction.upper()} | "
            f"진입가: {entry_price:.4f} | ATR: {atr:.4f}"
        )

        signals.append({
            "strategy":    strategy,
            "signal":      True,
            "direction":   signal_direction,
            "entry_price": entry_price,
            "atr":         atr,
        })

    return signals
