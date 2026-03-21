"""
core/signal_arbiter.py — 필터링 + Score 정렬 + 심볼 충돌 해소 (v5.0)

[v5.0] WFA Score 기반 충돌 해소로 전면 교체
  - 기존: Sharpe 비율 기반 심볼 충돌 해소
  - 변경: WFA 종합 Score 기반 심볼 충돌 해소
    Score = (survived_windows×2) + (min_calmar×3) + ln(1+avg_calmar)
  - 동일 심볼 복수 신호 → Score 최고 1개만 선택
  - 모든 전략이 BTCUSDT 15m → 심볼 충돌 = 1개만 실행
  - TP/SL 계산: 기존 fixed/atr 구조 유지 (모든 WFA 전략은 fixed)

변경사항:
  v5.0: Sharpe → Score, 단일 심볼 최적화, 보고서 순위 반영
  v2.5: Sharpe 기반 (이전 버전)
"""

from config import MIN_NOTIONAL, CAPITAL_ALLOCATION
from utils.logger import get_logger

logger = get_logger("signal_arbiter")

# ── 수수료 상수 ────────────────────────────────────────────────────
TAKER_FEE_RATE  = 0.00045   # 0.045%
ROUND_TRIP_FEE  = TAKER_FEE_RATE * 2   # 0.09% (진입 + 청산 왕복)

# fixed TP 전략의 최소 순이익 기준 (마진 기준 %)
MIN_NET_PROFIT_PCT = 1.0   # 마진 기준 1% 이상


def calc_tp_sl(
    entry: float,
    atr: float | None,
    strategy: dict,
    direction: str = "long",
) -> tuple[float, float]:
    """
    TP/SL 가격 계산.

    LONG:
        fixed → tp = entry × (1 + tp_mult),  sl = entry × (1 - sl_mult)
        atr   → tp = entry + atr × tp_mult,  sl = entry - atr × sl_mult

    SHORT:
        fixed → tp = entry × (1 - tp_mult),  sl = entry × (1 + sl_mult)
        atr   → tp = entry - atr × tp_mult,  sl = entry + atr × sl_mult
    """
    tp_type = strategy.get("tp_type", "fixed")
    tp_mult = strategy.get("tp_mult", 0.010)
    sl_mult = strategy.get("sl_mult", 0.005)
    is_long = direction.lower() != "short"

    if tp_type == "atr":
        if not atr or atr <= 0:
            logger.warning(
                f"[ARBITER] {strategy['id']} ATR={atr} 비정상 → fixed 1%/0.5% 폴백"
            )
            if is_long:
                tp = entry * 1.010
                sl = entry * 0.995
            else:
                tp = entry * 0.990
                sl = entry * 1.005
        else:
            if is_long:
                tp = entry + atr * tp_mult
                sl = entry - atr * sl_mult
            else:
                tp = entry - atr * tp_mult
                sl = entry + atr * sl_mult
    else:  # "fixed"
        if is_long:
            tp = entry * (1 + tp_mult)
            sl = entry * (1 - sl_mult)
        else:
            tp = entry * (1 - tp_mult)
            sl = entry * (1 + sl_mult)

    return tp, sl


def _log_fee_analysis(
    strategy_id: str,
    entry: float,
    tp: float,
    sl: float,
    leverage: int,
    tp_type: str,
    direction: str = "long",
    score: float = 0.0,
) -> None:
    """
    [v5.0] 수수료 포함 순손익 분석 로그 출력.
    WFA 전략은 win_rate 없음 → Score 기반 로그로 교체.
    """
    fee_pct    = ROUND_TRIP_FEE * leverage * 100
    tp_move    = abs((tp - entry) / entry * 100)
    sl_move    = abs((sl - entry) / entry * 100)

    net_tp     = tp_move * leverage - fee_pct
    net_sl     = sl_move * leverage + fee_pct

    dir_label  = direction.upper()

    logger.info(
        f"[ARBITER] 💰 수수료 분석 {strategy_id} [{dir_label}] ({tp_type}) | "
        f"Score {score:.2f} | 레버리지 {leverage}x | 수수료(마진) {fee_pct:.2f}% | "
        f"순TP: +{net_tp:.1f}% | 순SL: -{net_sl:.1f}%"
    )


def arbitrate(signals: list, balance: float, open_positions: dict) -> list:
    """
    신호 필터링 후 Score 정렬된 실행 가능 신호 반환. (v5.0)

    [v5.0 변경점]
      - Sharpe → Score 기반 정렬 및 충돌 해소
      - 동일 심볼 복수 신호 시 Score 최고 1개만 실행
      - 다른 방향(LONG vs SHORT) 동시 신호도 Score 우선 1개만

    Args:
        signals:        generate_all_signals() 반환값
        balance:        현재 사용 가능 USDT (free balance)
        open_positions: {symbol: position_info} 현재 보유 포지션

    Returns:
        실행 가능한 신호 리스트 (Score 내림차순)
    """
    executable = []

    for sig in signals:
        strategy    = sig["strategy"]
        symbol      = strategy["symbol"]
        strategy_id = strategy["id"]
        leverage    = strategy["leverage"]
        score       = strategy.get("score", 0.0)
        entry       = sig["entry_price"]
        atr         = sig.get("atr")
        tp_type     = strategy.get("tp_type", "fixed")
        tp_mult     = strategy.get("tp_mult", 0.010)
        sl_mult     = strategy.get("sl_mult", 0.005)

        # ── 필터 1: 심볼 포지션 중복 ──────────────────────────
        if symbol in open_positions:
            logger.info(f"[ARBITER] SKIP-POS | {strategy_id} — {symbol} 포지션 보유 중")
            continue

        # ── 필터 2: 최소 명목가치 ─────────────────────────────
        alloc    = CAPITAL_ALLOCATION.get(symbol, 0)
        margin   = balance * alloc
        notional = margin * leverage
        min_not  = MIN_NOTIONAL.get(symbol, 100)

        if notional < min_not:
            logger.info(
                f"[ARBITER] WATCH-ONLY | {strategy_id} — "
                f"명목가치 ${notional:.1f} < 최소 ${min_not}"
            )
            continue

        # ── TP/SL 계산 ───────────────────────────────────────
        direction = sig.get("direction", "long")
        tp, sl = calc_tp_sl(entry, atr, strategy, direction=direction)

        is_long = direction.lower() != "short"

        # TP/SL 유효성 필터
        if is_long:
            if tp <= entry:
                logger.warning(f"[ARBITER] {strategy_id} LONG TP({tp:.4f}) <= entry({entry:.4f}) → 스킵")
                continue
            if sl >= entry:
                logger.warning(f"[ARBITER] {strategy_id} LONG SL({sl:.4f}) >= entry({entry:.4f}) → 스킵")
                continue
        else:
            if tp >= entry:
                logger.warning(f"[ARBITER] {strategy_id} SHORT TP({tp:.4f}) >= entry({entry:.4f}) → 스킵")
                continue
            if sl <= entry:
                logger.warning(f"[ARBITER] {strategy_id} SHORT SL({sl:.4f}) <= entry({entry:.4f}) → 스킵")
                continue

        # ── 필터 3: fixed TP 수수료 순이익 체크 ────────
        if tp_type == "fixed":
            tp_move_pct = abs((tp - entry) / entry * 100)
            fee_pct     = ROUND_TRIP_FEE * leverage * 100
            net_tp_pct  = tp_move_pct * leverage - fee_pct

            if net_tp_pct < MIN_NET_PROFIT_PCT:
                logger.warning(
                    f"[ARBITER] SKIP-FEE | {strategy_id} — "
                    f"순TP이익 {net_tp_pct:.2f}% < 최소 {MIN_NET_PROFIT_PCT}% "
                    f"(TP {tp_move_pct:.2f}% × {leverage}x - 수수료 {fee_pct:.2f}%)"
                )
                continue

        # ── TP/SL 로그 ──────────────────────────────────────
        dir_label = "LONG" if is_long else "SHORT"
        logger.info(
            f"[ARBITER] {strategy_id} [{dir_label}] | "
            f"Score: {score:.2f} | "
            f"전략 TP/SL: {tp_mult*100:.1f}%/{sl_mult*100:.1f}% (WFA 검증) | "
            f"TP={tp:.4f} ({(tp/entry-1)*100:+.2f}%) | "
            f"SL={sl:.4f} ({(sl/entry-1)*100:+.2f}%)"
        )

        # ── 수수료 분석 로그 ───────────────────────────
        _log_fee_analysis(strategy_id, entry, tp, sl, leverage, tp_type, direction, score)

        executable.append({
            **sig,
            "tp":        tp,
            "sl":        sl,
            "margin":    margin,
            "notional":  notional,
            "score":     score,
            "direction": direction,
        })

    # ── [v5.0] Score 기반 심볼 충돌 해소 ──────────────────────
    # 같은 심볼에 여러 전략 신호 → Score 최고 1개만 선택
    # 모든 전략이 BTC/USDT 15m이므로, 실질적으로 1루프 최대 1개 신호 실행
    executable.sort(key=lambda x: x["score"], reverse=True)

    seen_symbols: dict = {}
    deduplicated = []

    for sig in executable:
        symbol      = sig["strategy"]["symbol"]
        strategy_id = sig["strategy"]["id"]
        score       = sig["score"]

        if symbol in seen_symbols:
            winner_id = seen_symbols[symbol]
            logger.info(
                f"[ARBITER] SKIP-SCORE-CONFLICT | {strategy_id} (Score {score:.2f}) — "
                f"{symbol} 이미 {winner_id} 선택됨 (더 높은 Score)"
            )
            continue

        seen_symbols[symbol] = strategy_id
        deduplicated.append(sig)

    if deduplicated:
        logger.info(
            f"[ARBITER] 🏆 최종 실행 신호 {len(deduplicated)}개 (Score 충돌 해소 후):"
        )
        for i, s in enumerate(deduplicated):
            sid = s["strategy"]["id"]
            logger.info(
                f"[ARBITER]   #{i+1} {sid} [{s['direction'].upper()}] "
                f"(Score {s['score']:.2f}) | "
                f"TP {s['tp']:.4f} ({s['strategy']['tp_mult']*100:.1f}%) | "
                f"SL {s['sl']:.4f} ({s['strategy']['sl_mult']*100:.1f}%)"
            )
    else:
        logger.info("[ARBITER] 실행 가능 신호 없음 (필터링 후)")

    return deduplicated
