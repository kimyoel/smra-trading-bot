"""
core/signal_generator.py — 전략별 지표 AND 조건 → 신호 생성 (v3.2)

[v3.2] 타임프레임별 봉 마감 동기화
  - 기존: 5분마다 17개 전략 전부 지표 조회 (불필요한 API 호출 + 연산 낭비)
  - 변경: 각 전략의 타임프레임 봉이 마감될 때만 해당 전략 지표 조회
    - 15m 전략 (3개) → 15분 정각에만 (minute % 15 == 0)
    - 1h 전략 (11개) → 정시에만 (minute == 0)
    - 4h 전략 (3개)  → 4시간 정각에만 (hour % 4 == 0 and minute == 0)
  - 효과: API 호출량 ~75% 감소, 백테스트와 동일한 봉 마감 타이밍 보장
  - 참고: 5m 전략은 현재 없으나 추가 시 매 루프 실행됨

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
from datetime import datetime, timezone
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


# ── [v3.2] 타임프레임별 봉 마감 체크 ──────────────────────────
# 루프는 5분마다 실행되므로, 각 타임프레임이 마감되는 시점인지 확인
# 5m: 매번 (기본), 15m: 15분 경계, 1h: 정시, 4h: 4시간 경계
_TF_SECONDS = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400}


def _is_candle_boundary(timeframe: str, utc_now: datetime | None = None) -> bool:
    """
    현재 UTC 시각이 해당 타임프레임의 봉 마감 직후인지 판단.

    루프가 5분봉 마감 + 3초에 실행되므로:
      - 15m: minute in (0, 15, 30, 45)  → True
      - 1h:  minute == 0                → True
      - 4h:  hour % 4 == 0, minute == 0 → True
      - 5m:  항상 True (매 루프)

    Returns:
        True면 이번 루프에서 해당 타임프레임 전략을 평가해야 함.
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
        # 알 수 없는 타임프레임은 안전하게 매번 실행
        return True


def generate_all_signals() -> list[dict]:
    """
    config.ALL_STRATEGIES에 등록된 전략만 감시/매매. (v3.2)

    [v3.2 변경점]
      - 타임프레임별 봉 마감 시점에만 해당 전략 지표 조회
      - 15m: 15분마다, 1h: 1시간마다, 4h: 4시간마다
      - 봉이 마감되지 않은 타임프레임의 전략은 스킵 (API 절약)

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
    utc_now = datetime.now(timezone.utc)

    # ── [v3.1] config.ALL_STRATEGIES 기반 활성 전략 필터링 ────
    active_strategies = {}
    for sid in ALL_STRATEGIES:
        if sid in STRATEGY_REGISTRY:
            active_strategies[sid] = STRATEGY_REGISTRY[sid]
        else:
            logger.warning(f"[SIGNAL] ⚠️ ALL_STRATEGIES에 '{sid}' 있으나 REGISTRY에 미등록 → 무시")

    # ── [v3.2] 타임프레임별 봉 마감 필터링 ────────────────────
    # 현재 시각 기준으로 봉이 마감된 타임프레임의 전략만 남김
    eligible_strategies = {}
    skipped_tf_counts: dict[str, int] = {}   # 스킵된 타임프레임별 카운트
    for sid, strat in active_strategies.items():
        tf = strat["timeframe"]
        if _is_candle_boundary(tf, utc_now):
            eligible_strategies[sid] = strat
        else:
            skipped_tf_counts[tf] = skipped_tf_counts.get(tf, 0) + 1

    # 로그: 활성/스킵 현황
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

    # ── 병렬 pre-fetch: 봉 마감된 전략의 유니크 조합만 캐시 워밍 ──
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
