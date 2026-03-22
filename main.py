"""
main.py — SMRA Bot 메인 루프 (v6.3.4 — 텔레그램 알림 누락 수정)

v6.3.4:
  [FIX] 재진입 시 진입 알림 누락 수정
    → 청산 감지 시 _notified_entries에서도 해당 키 제거
    → 동일 전략 재진입 시 notify_entry 정상 발송
  [FIX] record_position_timeframe 예외 안전 처리
    → 파일 I/O 예외 발생해도 notify_entry까지 정상 도달

v6.3.3:
  [FIX] 헤지 모드 전환 실패 시 봇 종료하지 않고 One-way 호환 모드로 계속 동작
    - 기존 포지션 관리 기능 유지 (max_hold_bars 강제청산, ATR TP/SL 갱신, 청산 감지)
    - One-way 모드에서는 새 진입만 차단 (기존 포지션 보호)
    - 매 루프에서 포지션 0개 감지 시 자동 헤지 모드 전환 시도
    - 전환 성공 후 다음 루프부터 신규 진입 허용

v6.3.2:
  [FIX] 에러 알림 중복 전송 방지 (파일 기반 dedup)
    → Railway 재시작 시 동일 에러 알림 반복 차단 (쿨다운 1시간)

v6.3.1 (Hedge Mode 로직 수정):
  [FIX] 강제청산 시 cancel_all_open_orders(symbol, pos_side=direction) 변경
    → 동일 심볼 반대 방향 TP/SL 보존 (LONG↔SHORT 독립 관리)
  [FIX] notify_entry 중복 방지 로직 수정
    → _notified_entries discard 순서 변경 (재진입 시에만 초기화)

v6.3 (Hedge Mode 전면 전환):
  [HEDGE] 헤지 모드(dualSidePosition=true) 적용
  - 동일 심볼에 LONG + SHORT 독립 포지션 최대 1개씩 허용
  - 중복 진입 방지: (symbol, direction) 복합 키 기준
  - 포지션 키: "symbol:LONG" / "symbol:SHORT" 형태
  - 봇 시작 시 ensure_hedge_mode() 1회 호출 (안전한 모드 전환)
  - 중복진입 추적을 executed_pos_keys로 교체: (symbol, direction) 추적
  - 청산 감지: pos_key 기반 _prev_open_positions 비교
  - 강제청산: pos_key 기반 max_hold_bars 체크

v6.2:
  [XRP 4h 추가] XRPUSDT_4h_WFA_Report.docx 기반 XRP 4시간봉 전략 10개 추가
  - BTC 40개 + ETH 40개 + XRP 40개 = 총 120개 전략
v6.1:
  [XRP 1h 추가] XRPUSDT_1h_WFA_Report.docx 기반 XRP 1시간봉 전략 10개 추가
v6.0:
  [XRP 15m 추가] XRPUSDT_15m_WFA_Report.docx 기반 XRP 15분봉 전략 10개 추가
v2.6: 봉 마감 정각 동기화 (wait_for_candle_close)
v2.7: 신호 TTL → 봉 경계 체크로 대체, 파일 기반 entry_time (v2.9)
v2.8:
  [수정] 강제청산 시 close_position_market() 내부에서 Binance 실시간 size 재조회
v2.9:
  [FIX] 1심볼 2중 진입 완전 차단 — executed_pos_keys set 도입
v2.11:
  [FIX] 1루프 1심볼 제한 break 제거 → 동일 루프 내 여러 심볼 동시 진입 허용
v2.12:
  [FIX] 익절/손절 텔레그램 알림 누락 수정
v2.13:
  [FIX] signal_arbiter v5.0 연계 — Score 기반 심볼 충돌 해소
v2.14:
  [FIX] 고정 24봉 강제청산 → 전략별 max_hold_bars 동적 적용
v2.15:
  [FIX] 타임프레임별 봉 마감 동기화
v2.16:
  [최적화] 5분봉 루프 → 15분봉 루프로 변경
v2.18:
  [FIX] 텔레그램 알림 중복 발송 완전 수정
"""

import time
import traceback
from datetime import datetime, timezone

from config import LOOP_INTERVAL_SEC
from strategies.registry import STRATEGY_REGISTRY
from core.data_manager import get_balance, clear_cache, ensure_hedge_mode, try_switch_hedge_mode, is_hedge_mode
from core.signal_generator import generate_all_signals
from core.signal_arbiter import arbitrate
from core.position_manager import (
    get_open_positions, get_position_age_bars, record_position_timeframe,
    make_pos_key, parse_pos_key,
)
from core.order_manager import execute_order, cancel_all_open_orders, close_position_market, update_atr_tp_sl, fetch_realized_pnl
from core.risk_manager import (
    check_circuit_breaker, increment_api_error, reset_api_error,
    update_strategy_mdd
)
from utils.logger import get_logger
from utils.notifier import notify_entry, notify_close, notify_error, notify_circuit_breaker

logger = get_logger("main")

# [v2.14] 타임프레임별 1봉당 시간 (강제청산 계산용)
# max_hold_bars × TF_BAR_HOURS[tf] = 최대 보유 시간(h)
TF_BAR_HOURS = {"5m": 1/12, "15m": 0.25, "1h": 1.0, "4h": 4.0}

# [v5.2] 봉 마감 동기화 설정 — 5분봉 기준
CANDLE_TF_SEC = 5 * 60   # 기준: 5분봉 (300초)
CANDLE_OFFSET = 3         # 봉 마감 후 3초 뒤 실행

# [v2.12] 루프 간 포지션 상태 추적 (청산 감지용)
# [v6.3] 키: "symbol:LONG" / "symbol:SHORT" 복합 키
_prev_open_positions: dict = {}

# [v2.18] 중복 알림 방지 — 이미 알림 발송한 청산/진입 건 기록
# [v6.3] key 형식: "symbol:DIRECTION:strategy_id"
_notified_closes: set = set()
_notified_entries: set = set()


def wait_for_candle_close() -> None:
    """
    [v5.2] 다음 5분봉 마감 후 CANDLE_OFFSET초에 맞춰 sleep.
    """
    now = time.time()
    next_close = (int(now / CANDLE_TF_SEC) + 1) * CANDLE_TF_SEC
    sleep_sec  = next_close + CANDLE_OFFSET - now
    wake_utc   = datetime.fromtimestamp(next_close + CANDLE_OFFSET, tz=timezone.utc)
    logger.info(
        f"[LOOP] ⏱ 다음 5분봉 마감 대기: {sleep_sec:.1f}초 "
        f"(기상 시각 {wake_utc.strftime('%H:%M:%S')} UTC)"
    )
    time.sleep(max(0, sleep_sec))


def _current_candle_id() -> int:
    """현재 5분봉 ID (Unix timestamp를 300으로 나눈 정수)"""
    return int(time.time() / CANDLE_TF_SEC)


def run_loop() -> None:
    """단일 루프 실행 (v6.3: Hedge Mode — pos_key 기반 독립 포지션 관리)"""
    global _prev_open_positions
    candle_id_at_start = _current_candle_id()
    logger.info("=" * 60)
    logger.info("[LOOP] 루프 시작 (Hedge Mode)")

    # ── 1. 캐시 초기화 (루프당 1회) ──────────────────────────
    clear_cache()

    # ── 2. 잔고 조회 ──────────────────────────────────────────
    balance_total, balance_free = get_balance()
    if balance_total <= 0:
        logger.warning("[LOOP] 잔고 0 또는 조회 실패 — 이번 루프 스킵")
        _update_prev_snapshot(open_positions={})
        return
    logger.info(
        f"[LOOP] 잔고 | total=${balance_total:.2f} USDT | "
        f"free=${balance_free:.2f} USDT"
    )

    # ── 3. 현재 포지션 조회 (v6.3: pos_key 기반) ────────────
    open_positions = get_open_positions()
    pos_keys_list = list(open_positions.keys())
    logger.info(f"[LOOP] 보유 포지션: {pos_keys_list or '없음'}")

    # ── 3-0. [v6.3.3] 헤지 모드 자동 전환 시도 ───────────────
    # One-way 모드이고 포지션이 0개이면 전환 시도
    if not is_hedge_mode():
        if len(open_positions) == 0:
            logger.info("[LOOP] 🔄 포지션 0개 감지 — 헤지 모드 전환 시도")
            switched = try_switch_hedge_mode()
            if switched:
                logger.info("[LOOP] ✅ 헤지 모드 전환 성공! 다음 루프부터 신규 진입 허용")
                notify_error("✅ 헤지 모드 전환 완료! 신규 진입 재개됩니다.")
            else:
                logger.info("[LOOP] ⏳ 헤지 모드 전환 실패 — 다음 루프 재시도")
        else:
            logger.info(
                f"[LOOP] ⏳ One-way 모드 유지 — 포지션 {len(open_positions)}개 보유 중 "
                f"(max_hold_bars 청산 대기)"
            )

    # ── 3-1. [v6.3] 청산 감지 — pos_key 기반 비교 ────────────
    _force_closed_this_loop: set = set()
    for prev_key, prev_info in _prev_open_positions.items():
        if prev_key not in open_positions:
            strat_id   = prev_info.get("strategy_id", "UNKNOWN")
            close_key  = f"{prev_key}:{strat_id}"

            if close_key in _notified_closes:
                logger.debug(f"[LOOP] {prev_key} 청산 알림 이미 발송됨 → 스킵")
                continue

            symbol, direction = parse_pos_key(prev_key)
            entry_time = prev_info.get("entry_time", 0)
            prev_tf    = prev_info.get("timeframe", "")
            pnl        = fetch_realized_pnl(symbol, entry_time)
            result_lbl = "✅ 익절" if pnl > 0 else "❌ 손절"
            notify_close(strat_id, f"{symbol} [{direction.upper()}]", result_lbl, pnl, timeframe=prev_tf)
            _notified_closes.add(close_key)
            # [v6.3.4] 청산 완료 → 진입 알림 기록 제거 (재진입 시 알림 정상 발송)
            _notified_entries.discard(close_key)
            logger.info(f"[LOOP] {prev_key} 청산 감지 (TP/SL) → 텔레그램 알림 (PnL={pnl:+.4f})")

    # ── 4. max_hold_bars 초과 포지션 강제 청산 (v6.3: pos_key) ─
    for pos_key, pos_info in list(open_positions.items()):
        symbol, direction = parse_pos_key(pos_key)
        tf            = pos_info.get("timeframe", "1h")
        strategy_id   = pos_info.get("strategy_id", "UNKNOWN")
        bar_hours     = TF_BAR_HOURS.get(tf, 1.0)
        age_h         = get_position_age_bars(pos_key)

        strat = STRATEGY_REGISTRY.get(strategy_id, {})
        max_hold_bars = strat.get("max_hold_bars", 48)
        max_hours     = max_hold_bars * bar_hours

        if age_h > max_hours:
            logger.warning(
                f"[LOOP] {pos_key} {age_h:.1f}h 초과 "
                f"(기준: {max_hours:.1f}h = {tf} {max_hold_bars}봉) → 강제 청산"
            )
            notify_circuit_breaker(
                "POSITION_TIMEOUT",
                f"{pos_key} {age_h:.1f}h 초과 → {tf} {max_hold_bars}봉 기준 강제 청산 ({strategy_id})"
            )
            cancel_all_open_orders(symbol, pos_side=direction)
            close_position_market(symbol, pos_side=direction)

            force_pnl   = float(pos_info.get("unrealized_pnl", 0.0))
            result_lbl  = "✅ 익절" if force_pnl > 0 else "❌ 손절"
            notify_close(strategy_id, f"{symbol} [{direction.upper()}]",
                         f"⏰ {max_hold_bars}봉 강제청산 ({result_lbl})", force_pnl, timeframe=tf)
            force_close_key = f"{pos_key}:{strategy_id}"
            _notified_closes.add(force_close_key)
            # [v6.3.4] 강제청산 완료 → 진입 알림 기록 제거 (재진입 시 알림 정상 발송)
            _notified_entries.discard(force_close_key)
            _force_closed_this_loop.add(pos_key)

    # ── 4-1. ATR 전략 TP/SL 매 봉 갱신 ──────────────────────
    open_positions_after_close = get_open_positions()
    if is_hedge_mode():
        update_atr_tp_sl(open_positions_after_close)

    # ── 4-2. [v6.3.3] One-way 모드 — 새 진입 차단 ────────────
    if not is_hedge_mode():
        logger.info(
            "[LOOP] ⏳ One-way 호환 모드 — 기존 포지션 관리만 수행, "
            "신호 생성/신규 진입 스킵"
        )
        _update_prev_snapshot(open_positions, _force_closed_this_loop)
        return

    # ── 5. 신호 생성 ────────────────────────────────────────
    try:
        signals = generate_all_signals()
        reset_api_error()
    except Exception as e:
        err_cnt = increment_api_error()
        logger.error(f"[LOOP] 신호 생성 오류 (누적 {err_cnt}회): {e}")
        if err_cnt >= 5:
            notify_circuit_breaker("API_ERROR_FLOOD", f"연속 {err_cnt}회 오류")
            time.sleep(60)
        _update_prev_snapshot(open_positions)
        return

    logger.info(f"[LOOP] 신호 발생: {len(signals)}개")

    # ── 6. Arbiter 필터링 (v6.3: pos_key 기반 중복 체크) ─────
    executable = arbitrate(signals, balance_total, open_positions)
    logger.info(f"[LOOP] 실행 가능 신호: {len(executable)}개")

    if not executable:
        logger.info("[LOOP] 실행할 신호 없음")
        _update_prev_snapshot(open_positions)
        return

    # ── 7. Score 순 실행 (v6.3: executed_pos_keys 추적) ──────
    order_placed = False
    # [v6.3] (symbol, direction) 복합 키로 중복 진입 추적
    #         동일 심볼이라도 반대 방향은 독립 허용
    executed_pos_keys: set = set()

    for top_sig in executable:
        strategy    = top_sig["strategy"]
        symbol      = strategy["symbol"]
        strategy_id = strategy["id"]
        leverage    = strategy["leverage"]
        base_mdd    = strategy["base_mdd"]
        timeframe   = strategy["timeframe"]
        direction   = top_sig.get("direction", "long")
        pos_key     = make_pos_key(symbol, direction)

        # [v6.3] 동일 (심볼, 방향) 중복 진입 차단
        if pos_key in executed_pos_keys:
            logger.warning(
                f"[LOOP] ⚠️ 2중진입 차단: {strategy_id} | {pos_key} "
                f"이번 루프에서 이미 execute_order 호출됨 → 스킵"
            )
            continue

        # ── 봉 경계 체크 ─────────────────────────────────────
        current_candle = _current_candle_id()
        if current_candle != candle_id_at_start:
            elapsed = (current_candle - candle_id_at_start) * CANDLE_TF_SEC
            logger.warning(
                f"[LOOP] ⏰ 봉 경계 초과 — {elapsed/60:.0f}분 경과 "
                f"→ {strategy_id} 이후 포기, 다음 봉 대기"
            )
            break

        # ── 8. Circuit Breaker 체크 ──────────────────────────
        cb = check_circuit_breaker(symbol, strategy_id, base_mdd)

        if cb["block"]:
            logger.warning(
                f"[LOOP] CB 발동 — {cb['reason']} ({cb['action']}) "
                f"→ {strategy_id} 스킵, 다음 신호 시도"
            )
            continue

        if cb.get("action") == "REDUCE_LEVERAGE_50PCT":
            reduced_lev = max(1, leverage // 2)
            top_sig["strategy"] = {**strategy, "leverage": reduced_lev}
            logger.info(f"[LOOP] 펀딩비 높음 → 레버리지 {leverage}x → {reduced_lev}x")

        # ── 9. MDD 업데이트 ──────────────────────────────────
        update_strategy_mdd(strategy_id, balance_total, base_mdd)

        # ── 9-1. free 잔고 검증 ──────────────────────────────
        required_margin = top_sig["margin"]
        if balance_free < required_margin:
            logger.warning(
                f"[LOOP] ⚠️ 여유잔고 부족 — {strategy_id} | "
                f"필요 마진 ${required_margin:.2f} > free ${balance_free:.2f} → 스킵"
            )
            continue

        # ── 10. 주문 실행 ────────────────────────────────────
        entry = top_sig['entry_price']
        tp    = top_sig['tp']
        sl    = top_sig['sl']
        dir_label = direction.upper()
        logger.info(
            f"[LOOP] 주문 실행: {strategy_id} [{dir_label}] | {symbol} | "
            f"진입가 {entry:.4f} | "
            f"TP {tp:.4f} (+{(tp/entry-1)*100:.2f}%) | "
            f"SL {sl:.4f} ({(sl/entry-1)*100:.2f}%)"
        )

        executed_pos_keys.add(pos_key)   # 호출 즉시 등록
        success = execute_order(top_sig)

        if success:
            # ✅ 진입 성공 → 기록 (v6.3.4: 예외 안전)
            try:
                record_position_timeframe(symbol, timeframe, strategy_id, direction=direction)
            except Exception as rec_err:
                logger.warning(f"[LOOP] record_position_timeframe 오류 (진입은 성공): {rec_err}")

            # 알림 기록 클리어 (재진입이므로 이전 청산 알림 초기화)
            notify_key = f"{pos_key}:{strategy_id}"
            _notified_closes.discard(notify_key)

            # 진입 알림 1회만 발송
            if notify_key not in _notified_entries:
                notify_entry(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    side=dir_label,
                    entry=entry,
                    tp=tp,
                    sl=sl,
                    leverage=top_sig["strategy"]["leverage"],
                    margin=top_sig["margin"],
                    timeframe=timeframe,
                )
                _notified_entries.add(notify_key)
            logger.info(f"[LOOP] ✅ 주문 완료: {strategy_id} [{dir_label}]")
            order_placed = True
        else:
            logger.error(f"[LOOP] ❌ 주문 실패: {strategy_id} → {pos_key} 이번 루프 재시도 금지")

    if not order_placed:
        logger.info("[LOOP] 모든 신호 시도 완료 (주문 없음)")

    # ── 루프 끝: 현재 포지션 스냅샷 저장 ─────────────────────
    _update_prev_snapshot(open_positions, _force_closed_this_loop)


def _update_prev_snapshot(
    open_positions: dict,
    force_closed: set | None = None,
) -> None:
    """
    [v6.3] _prev_open_positions 스냅샷 갱신 (pos_key 기반).
    """
    global _prev_open_positions
    snapshot = dict(open_positions)
    if force_closed:
        for key in force_closed:
            snapshot.pop(key, None)
    _prev_open_positions = snapshot


def main() -> None:
    logger.info("🚀 SMRA Bot v6.3.4 시작 (Hedge Mode + One-way 호환)")
    logger.info(f"120개 전략 (BTC 40 + ETH 40 + XRP 40) | Hedge Mode | Score 순위 충돌 해소")

    # [v6.3.3] 헤지 모드 전환 시도 — 실패해도 봇 계속 동작
    ensure_hedge_mode()
    if is_hedge_mode():
        logger.info("[MAIN] ✅ 헤지 모드 활성 — 전체 기능 정상 가동")
    else:
        logger.warning(
            "[MAIN] ⚠️ One-way 호환 모드로 시작 — "
            "기존 포지션 관리 계속, 새 진입 차단. "
            "포지션 모두 청산되면 자동 헤지 전환 후 신규 진입 재개."
        )
        notify_error(
            "⚠️ One-way 호환 모드 시작\n"
            "기존 포지션 관리 계속 (강제청산, TP/SL 관리)\n"
            "포지션 모두 청산 후 자동 헤지 전환 예정"
        )

    while True:
        start = time.time()
        try:
            run_loop()
        except Exception as e:
            err_msg = f"루프 예외: {e}\n{traceback.format_exc()}"
            logger.error(err_msg)
            notify_error(err_msg)

        elapsed = time.time() - start
        logger.info(f"[LOOP] 완료 ({elapsed:.1f}초 소요)")
        wait_for_candle_close()


if __name__ == "__main__":
    main()
