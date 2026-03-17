"""
main.py — SMRA Bot 메인 루프 (v2.1 final)

진입 성공 시 record_position_timeframe() 호출 추가
→ position_manager가 타임프레임별 청산 시간 계산에 활용
"""

import time
import traceback

from config import LOOP_INTERVAL_SEC
from core.data_manager import get_balance, clear_cache
from core.signal_generator import generate_all_signals
from core.signal_arbiter import arbitrate
from core.position_manager import (
    get_open_positions, get_position_age_bars, record_position_timeframe
)
from core.order_manager import execute_order, cancel_all_open_orders, close_position_market
from core.risk_manager import (
    check_circuit_breaker, increment_api_error, reset_api_error,
    update_strategy_mdd
)
from utils.logger import get_logger
from utils.notifier import notify_entry, notify_error, notify_circuit_breaker

logger = get_logger("main")

# 백테스트 기준: max_hold_bars = 24봉 → 타임프레임별 시간
TF_HOURS = {"5m": 2.0, "15m": 6.0, "1h": 24.0}


def run_loop() -> None:
    """단일 루프 실행"""
    logger.info("=" * 60)
    logger.info("[LOOP] 루프 시작")

    # ── 1. 캐시 초기화 (루프당 1회) ──────────────────────────
    clear_cache()

    # ── 2. 잔고 조회 (free balance) ──────────────────────────
    balance = get_balance()
    if balance <= 0:
        logger.warning("[LOOP] 잔고 0 또는 조회 실패 — 이번 루프 스킵")
        return
    logger.info(f"[LOOP] 현재 잔고: ${balance:.2f} USDT (free)")

    # ── 3. 현재 포지션 조회 ───────────────────────────────────
    open_positions = get_open_positions()
    logger.info(f"[LOOP] 보유 포지션: {list(open_positions.keys()) or '없음'}")

    # ── 4. 24봉 초과 포지션 강제 청산 ────────────────────────
    for symbol, pos_info in list(open_positions.items()):
        tf        = pos_info.get("timeframe", "1h")
        max_hours = TF_HOURS.get(tf, 24.0)
        age_h     = get_position_age_bars(symbol)

        if age_h > max_hours:
            logger.warning(
                f"[LOOP] {symbol} {age_h:.1f}h 초과 "
                f"(기준: {max_hours}h = {tf} 24봉) → 강제 청산"
            )
            notify_circuit_breaker(
                "POSITION_TIMEOUT",
                f"{symbol} {age_h:.1f}h 초과 → {tf} 24봉 기준 강제 청산"
            )
            cancel_all_open_orders(symbol)
            close_position_market(symbol, pos_info["size"])

    # ── 5. 신호 생성 ──────────────────────────────────────────
    try:
        signals = generate_all_signals()
        reset_api_error()
    except Exception as e:
        err_cnt = increment_api_error()
        logger.error(f"[LOOP] 신호 생성 오류 (누적 {err_cnt}회): {e}")
        if err_cnt >= 5:
            notify_circuit_breaker("API_ERROR_FLOOD", f"연속 {err_cnt}회 오류")
            time.sleep(60)
        return

    logger.info(f"[LOOP] 신호 발생: {len(signals)}개")

    # ── 6. Arbiter 필터링 ─────────────────────────────────────
    executable = arbitrate(signals, balance, open_positions)
    logger.info(f"[LOOP] 실행 가능 신호: {len(executable)}개")

    if not executable:
        logger.info("[LOOP] 실행할 신호 없음")
        return

    # ── 7. Sharpe 순 실행 (CB 발동 시 다음 신호 폴오버) ───────
    order_placed = False
    for top_sig in executable:
        strategy    = top_sig["strategy"]
        symbol      = strategy["symbol"]
        strategy_id = strategy["id"]
        leverage    = strategy["leverage"]
        base_mdd    = strategy["base_mdd"]
        timeframe   = strategy["timeframe"]

        # ── 8. Circuit Breaker 체크 ────────────────────────────
        cb = check_circuit_breaker(symbol, strategy_id, base_mdd)

        if cb["block"]:
            logger.warning(
                f"[LOOP] CB 발동 — {cb['reason']} ({cb['action']}) "
                f"→ {strategy_id} 스킵, 다음 신호 시도"
            )
            continue

        # 펀딩비 높음 → 레버리지 50% 감소
        if cb.get("action") == "REDUCE_LEVERAGE_50PCT":
            reduced_lev = max(1, leverage // 2)
            top_sig["strategy"] = {**strategy, "leverage": reduced_lev}
            logger.info(f"[LOOP] 펀딩비 높음 → 레버리지 {leverage}x → {reduced_lev}x")

        # ── 9. MDD 업데이트 ────────────────────────────────────
        update_strategy_mdd(strategy_id, balance, base_mdd)

        # ── 10. 주문 실행 ─────────────────────────────────────
        entry = top_sig['entry_price']
        tp    = top_sig['tp']
        sl    = top_sig['sl']
        logger.info(
            f"[LOOP] 주문 실행: {strategy_id} | {symbol} | "
            f"진입가 {entry:.4f} | "
            f"TP {tp:.4f} (+{(tp/entry-1)*100:.2f}%) | "
            f"SL {sl:.4f} ({(sl/entry-1)*100:.2f}%)"
        )

        success = execute_order(top_sig)

        if success:
            # ✅ 진입 성공 → 타임프레임 기록 (24봉 청산 계산용)
            record_position_timeframe(symbol, timeframe)

            notify_entry(
                strategy_id=strategy_id,
                symbol=symbol,
                side="LONG",
                entry=entry,
                tp=tp,
                sl=sl,
                leverage=top_sig["strategy"]["leverage"],
                margin=top_sig["margin"],
            )
            logger.info(f"[LOOP] ✅ 주문 완료: {strategy_id}")
            order_placed = True
            break
        else:
            logger.error(f"[LOOP] ❌ 주문 실패: {strategy_id} → 다음 신호 시도")

    if not order_placed:
        logger.info("[LOOP] 모든 신호 시도 완료 (주문 없음)")


def main() -> None:
    logger.info("🚀 SMRA Bot v2.1 시작 (No-Phase Architecture)")
    logger.info(f"루프 간격: {LOOP_INTERVAL_SEC}초 | 최대 보유: 24봉 기준 (5m=2h / 15m=6h / 1h=24h)")

    while True:
        start = time.time()
        try:
            run_loop()
        except Exception as e:
            err_msg = f"루프 예외: {e}\n{traceback.format_exc()}"
            logger.error(err_msg)
            notify_error(err_msg)

        elapsed = time.time() - start
        sleep_t = max(0, LOOP_INTERVAL_SEC - elapsed)
        logger.info(f"[LOOP] 완료 ({elapsed:.1f}초 소요) → {sleep_t:.1f}초 대기\n")
        time.sleep(sleep_t)


if __name__ == "__main__":
    main()
