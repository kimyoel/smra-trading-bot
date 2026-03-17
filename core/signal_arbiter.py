"""
core/signal_arbiter.py — 필터링 + Sharpe 정렬 (v2.1)

변경사항:
  - calc_tp_sl(): H코드 문자열 대신 strategy의 tp_type/tp_mult/sl_mult 직접 사용
  - ATR=0 또는 None 방어 코드 추가
  - 마진 계산 시 free balance 기반 (balance는 get_balance()에서 free 잔고 반환 전제)
"""

from config import MIN_NOTIONAL, CAPITAL_ALLOCATION
from utils.logger import get_logger

logger = get_logger("signal_arbiter")


def calc_tp_sl(entry: float, atr: float | None, strategy: dict) -> tuple[float, float]:
    """
    TP/SL 가격 계산.

    tp_type="fixed":
        tp = entry × (1 + tp_mult)
        sl = entry × (1 - sl_mult)
        예: tp_mult=0.010, sl_mult=0.005 → entry×1.01 / entry×0.995

    tp_type="atr":
        tp = entry + atr × tp_mult
        sl = entry - atr × sl_mult
        예: tp_mult=2.0, sl_mult=1.0 → entry+ATR×2 / entry-ATR×1

    ATR가 None이거나 0인 경우 → fixed fallback (±1% / ±0.5%)
    """
    tp_type = strategy.get("tp_type", "fixed")
    tp_mult = strategy.get("tp_mult", 0.010)
    sl_mult = strategy.get("sl_mult", 0.005)

    if tp_type == "atr":
        # ATR 유효성 체크
        if not atr or atr <= 0:
            logger.warning(
                f"[ARBITER] {strategy['id']} ATR={atr} 비정상 → fixed 1%/0.5% 폴백"
            )
            tp = entry * 1.010
            sl = entry * 0.995
        else:
            tp = entry + atr * tp_mult
            sl = entry - atr * sl_mult
    else:  # "fixed"
        tp = entry * (1 + tp_mult)
        sl = entry * (1 - sl_mult)

    return tp, sl


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
        entry       = sig["entry_price"]
        atr         = sig.get("atr")

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

        # ── TP/SL 계산 (직접 수치) ────────────────────────────
        tp, sl = calc_tp_sl(entry, atr, strategy)

        # TP가 진입가보다 낮거나 SL이 진입가보다 높은 경우 필터 (데이터 이상)
        if tp <= entry:
            logger.warning(f"[ARBITER] {strategy_id} TP({tp:.4f}) <= entry({entry:.4f}) → 스킵")
            continue
        if sl >= entry:
            logger.warning(f"[ARBITER] {strategy_id} SL({sl:.4f}) >= entry({entry:.4f}) → 스킵")
            continue

        # TP/SL 로그 (명시적 수치 출력)
        logger.info(
            f"[ARBITER] {strategy_id} TP={tp:.4f} (+{(tp/entry-1)*100:.2f}%) | "
            f"SL={sl:.4f} ({(sl/entry-1)*100:.2f}%)"
        )

        executable.append({
            **sig,
            "tp":       tp,
            "sl":       sl,
            "margin":   margin,
            "notional": notional,
            "sharpe":   sharpe,
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
