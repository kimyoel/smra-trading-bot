"""
core/signal_arbiter.py — 필터링 + Sharpe 정렬 (v2.3)

변경사항:
  v2.1: H코드 문자열 대신 strategy의 tp_type/tp_mult/sl_mult 직접 사용
  v2.2:
  [FIX1] 수수료 포함 순이익 필터 추가
         - 바이낸스 taker 수수료: 진입+청산 왕복 0.09% (명목가치 기준)
         - 마진 기준 수수료 = 0.09% × leverage
         - fixed TP의 경우: 순이익(%) = TP가격% × leverage - 수수료%
           이것이 최소 기준(MIN_NET_PROFIT_PCT) 이상인지 체크
         - ATR 기반은 동적이라 필터는 생략하되 로그에 수수료 정보 출력
  [FIX2] arbitrate() 로그에 수수료 감안 순손익 표시
  v2.3:
  [FIX3] 롱/숏 양방향 TP/SL 계산 지원
         - calc_tp_sl()에 direction 파라미터 추가
         - SHORT: tp = entry × (1 - tp_mult), sl = entry × (1 + sl_mult)
         - SHORT ATR: tp = entry - atr × tp_mult, sl = entry + atr × sl_mult
         - TP/SL 유효성 필터도 direction 기반으로 수정
         - 수수료 분석 로그도 방향 표시 추가
"""

from config import MIN_NOTIONAL, CAPITAL_ALLOCATION
from utils.logger import get_logger

logger = get_logger("signal_arbiter")

# ── 수수료 상수 ────────────────────────────────────────────────────
# 바이낸스 USDT-M 선물 taker 수수료 (BNB 미적용 일반 기준)
TAKER_FEE_RATE  = 0.00045   # 0.045%
ROUND_TRIP_FEE  = TAKER_FEE_RATE * 2   # 0.09% (진입 + 청산 왕복)

# fixed TP 전략의 최소 순이익 기준 (마진 기준 %)
# 수수료의 최소 2배 이상 벌어야 의미 있음 (너무 낮으면 슬리피지·변동성에 잡힘)
MIN_NET_PROFIT_PCT = 1.0   # 마진 기준 1% 이상


def calc_tp_sl(
    entry: float,
    atr: float | None,
    strategy: dict,
    direction: str = "long",
) -> tuple[float, float]:
    """
    TP/SL 가격 계산. (v2.3: direction 파라미터 추가)

    LONG:
        fixed → tp = entry × (1 + tp_mult),  sl = entry × (1 - sl_mult)
        atr   → tp = entry + atr × tp_mult,  sl = entry - atr × sl_mult

    SHORT:
        fixed → tp = entry × (1 - tp_mult),  sl = entry × (1 + sl_mult)
        atr   → tp = entry - atr × tp_mult,  sl = entry + atr × sl_mult

    ATR가 None이거나 0인 경우 → fixed fallback (±1% / ±0.5%)
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
    win_rate: float,
) -> None:
    """
    [v2.2] 수수료 포함 순손익 분석 로그 출력.

    마진 기준 계산:
        수수료(%) = ROUND_TRIP_FEE × leverage × 100
        순TP이익(%) = TP가격이동% × leverage - 수수료%
        순SL손실(%) = SL가격이동% × leverage + 수수료%
        기대수익(%) = 승률 × 순TP이익 - (1-승률) × 순SL손실
    """
    fee_pct    = ROUND_TRIP_FEE * leverage * 100   # 마진 기준 수수료 %
    tp_move    = (tp - entry) / entry * 100         # TP 가격이동 %
    sl_move    = abs((sl - entry) / entry * 100)    # SL 가격이동 %

    net_tp     = tp_move * leverage - fee_pct       # 순TP이익 %
    net_sl     = sl_move * leverage + fee_pct       # 순SL손실 %
    ev         = win_rate * net_tp - (1 - win_rate) * net_sl   # 기대수익 %

    ev_flag = "✅" if ev > 0 else "⚠️"

    logger.info(
        f"[ARBITER] 💰 수수료 분석 {strategy_id} ({tp_type}) | "
        f"레버리지 {leverage}x | 수수료(마진) {fee_pct:.2f}% | "
        f"순TP: +{net_tp:.1f}% | 순SL: -{net_sl:.1f}% | "
        f"기대수익(승률{win_rate:.0%}): {ev:+.2f}% {ev_flag}"
    )


def arbitrate(signals: list, balance: float, open_positions: dict) -> list:
    """
    신호 필터링 후 Sharpe 정렬된 실행 가능 신호 반환.

    Args:
        signals:        generate_all_signals() 반환값
        balance:        현재 사용 가능 USDT (free balance)
        open_positions: {symbol: position_info} 현재 보유 포지션

    Returns:
        실행 가능한 신호 리스트 (Sharpe 내림차순)
        각 항목에 tp, sl, margin, notional, tp_price, sl_price 추가
    """
    executable = []

    for sig in signals:
        strategy    = sig["strategy"]
        symbol      = strategy["symbol"]
        strategy_id = strategy["id"]
        leverage    = strategy["leverage"]
        sharpe      = strategy["sharpe"]
        win_rate    = strategy.get("win_rate", 0.5)
        entry       = sig["entry_price"]
        atr         = sig.get("atr")
        tp_type     = strategy.get("tp_type", "fixed")

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

        # ── TP/SL 계산 (v2.3: direction 전달) ───────────────
        direction = sig.get("direction", "long")
        tp, sl = calc_tp_sl(entry, atr, strategy, direction=direction)

        is_long = direction.lower() != "short"

        # TP/SL 유효성 필터 (방향에 따라 체크 기준 반전)
        if is_long:
            if tp <= entry:
                logger.warning(f"[ARBITER] {strategy_id} LONG TP({tp:.4f}) <= entry({entry:.4f}) → 스킵")
                continue
            if sl >= entry:
                logger.warning(f"[ARBITER] {strategy_id} LONG SL({sl:.4f}) >= entry({entry:.4f}) → 스킵")
                continue
        else:  # short
            if tp >= entry:
                logger.warning(f"[ARBITER] {strategy_id} SHORT TP({tp:.4f}) >= entry({entry:.4f}) → 스킵")
                continue
            if sl <= entry:
                logger.warning(f"[ARBITER] {strategy_id} SHORT SL({sl:.4f}) <= entry({entry:.4f}) → 스킵")
                continue

        # ── [v2.2] 필터 3: fixed TP 수수료 순이익 체크 ────────
        # ATR 기반은 ATR에 따라 동적으로 변하므로 필터 생략 (로그만 출력)
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

        # ── TP/SL 로그 ────────────────────────────────────────
        dir_label = "LONG" if is_long else "SHORT"
        logger.info(
            f"[ARBITER] {strategy_id} [{dir_label}] TP={tp:.4f} ({(tp/entry-1)*100:+.2f}%) | "
            f"SL={sl:.4f} ({(sl/entry-1)*100:+.2f}%)"
        )

        # ── [v2.2] 수수료 분석 로그 ───────────────────────────
        _log_fee_analysis(strategy_id, entry, tp, sl, leverage, tp_type, win_rate)


        executable.append({
            **sig,
            "tp":        tp,
            "sl":        sl,
            "margin":    margin,
            "notional":  notional,
            "sharpe":    sharpe,
            "direction": direction,   # v2.3: sig에서 전달받은 방향 보존
        })

    # Sharpe 내림차순 정렬
    executable.sort(key=lambda x: x["sharpe"], reverse=True)

    if executable:
        top = executable[0]
        logger.info(
            f"[ARBITER] 최종 실행 신호: {top['strategy']['id']} "
            f"(Sharpe {top['sharpe']:.2f}) | "
            f"TP {top['tp']:.4f} | SL {top['sl']:.4f}"
        )

    return executable
