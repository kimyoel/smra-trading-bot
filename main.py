"""
main.py — SMRA Bot 메인 루프 (v5.0)

v2.6: 봉 마감 정각 동기화 (wait_for_candle_close)
v2.7: 신호 TTL → 봉 경계 체크로 대체, 파일 기반 entry_time (v2.9)
v2.8:
  [수정] 강제청산 시 close_position_market() 내부에서 Binance 실시간 size 재조회
         → pos_info["size"] 의존 제거 (부분청산 등 불일치 방지)
  [수정] cancel_all_open_orders() → 일반 주문 + Algo Order 동시 취소 (v2.14 연계)
v2.9:
  [FIX] 1심볼 2중 진입 완전 차단 — executed_symbols set 도입
         기존 취약점: execute_order 실패(TP/SL 등록 실패 → 긴급청산 실패) 후
         continue로 동일 심볼 다른 전략 재시도 → 2중 포지션 가능
         → 한 번이라도 execute_order 호출한 심볼은 이번 루프에서 재시도 금지
  [FIX] record_position_timeframe() → strategy_id 함께 저장 (v2.11 연계)
         → 24봉 강제청산 로그에 어떤 전략으로 진입했는지 표시
v2.11:
  [FIX] 1루프 1심볼 제한 break 제거 → 동일 루프 내 여러 심볼 동시 진입 허용
         동일 심볼 2중 진입 차단은 executed_symbols set 으로 계속 유지
  [FIX] 텔레그램 알림 side="LONG" 하드코딩 → direction 동적 처리 (LONG/SHORT 정확히 표시)
v2.12:
  [FIX] 익절/손절 텔레그램 알림 누락 수정
         - TP/SL Algo Order 체결 시 포지션 소멸을 다음 루프에서 감지
         - _prev_open_positions 모듈 변수로 루프 간 포지션 상태 추적
         - fetch_realized_pnl() 로 Binance Income API 실현 PnL 조회 후 notify_close() 발송
         - 24봉 강제청산 시: unrealized_pnl 기반 즉시 notify_close() 발송 + _prev에서 제거(중복 방지)
v2.15:
  [FIX] 타임프레임별 봉 마감 동기화 (signal_generator v3.2 연계)
         - 기존: 5분마다 17개 전략 전부 지표 조회 (불필요한 API 호출)
         - 변경: 각 전략의 타임프레임 봉 마감 시점에만 해당 전략 평가
           15m → 15분 정각, 1h → 정시, 4h → 4시간 정각
         - 효과: API 호출량 ~75% 감소 (비마감 루프에서 1h/4h 전략 스킵)
v2.16:
  [최적화] 5분봉 루프 → 15분봉 루프로 변경
         - 5m 전략 0개 → 최소 타임프레임 15m 기준으로 루프 주기 변경
         - CANDLE_TF_SEC: 300초(5분) → 900초(15분)
         - 루프 횟수: 288→96/일 (67% 감소), API 호출 추가 절감
         - 15m 전략은 매 루프 평가, 1h는 4번째마다, 4h는 16번째마다
         - 봉 경계 체크도 15분봉 ID 기준으로 전환
v2.14:
  [FIX] 고정 24봉 강제청산 → 전략별 max_hold_bars 동적 적용
         - registry.py의 max_hold_bars 필드 참조 (backtest_report_final.docx 기반)
         - 16개 전략: 48봉, XRP_4h_SHORT_MOM: 16봉
         - TF_HOURS 제거 → TF_BAR_HOURS로 교체 (1봉당 시간)
         - 강제청산 기준: max_hold_bars x bar_hours
v2.13:
  [FIX] signal_arbiter v5.0 연계 — Score 기반 심볼 충돌 해소
         - arbiter에서 동일 심볼 → Score 최고 1개만 반환
         - executed_symbols는 2중 방어 (arbiter가 놓치는 케이스 안전장치)로 유지
         - 전략별 최적 TP/SL 매칭: registry의 tp_mult/sl_mult → arbiter → order_manager 흐름 확인
v2.18:
  [FIX] 텔레그램 알림 중복 발송 완전 수정
v5.4:
  [4시간봉 추가] BTCUSDT_4h_WFA_Report.docx 기반 4시간봉 전략 10개 추가
  - 기존 15m 10개 + 5m 10개 + 1h 10개 + 4h 10개 = 총 40개 전략
  - 4h 전략: 48루프마다 평가 (5분×48=4시간)
  - 4h 레버리지: 이론=1/(SL%+0.5%), 권장=이론×80% (상한20x)
  - 4h 황금기준: surv≥6, avg_calmar≥2, min_calmar≥0.5 (443/1894개 통과)
  - 새 지표: CMF (Chaikin Money Flow)
  - 충돌 해소: 4h > 1h > 15m > 5m (큰 타임프레임 우선)
v5.3:
  [1시간봉 추가] BTCUSDT_1h_WFA_Report.docx 기반 1시간봉 전략 10개 추가
  - 기존 15m 10개 + 5m 10개 + 1h 10개 = 총 30개 전략
  - 1h 전략: 12루프마다 평가 (5분×12=1시간), 15m: 3루프마다, 5m: 매 루프
  - 1h 레버리지: 이론=1/(SL%+0.5%), 권장=이론×80% (상한20x, min_calmar≥1.5→+2)
  - 1h 황금기준: surv≥6, avg_calmar≥2, min_calmar≥0.5 (272/3194개 통과)
  - 새 지표: ROC (Rate of Change)
v5.2:
  [5분봉 추가] BTCUSDT_5m_WFA_Report.docx 기반 5분봉 전략 10개 추가
  - 기존 15m 10개 + 5m 10개 = 총 20개 전략
  - 루프 주기: 15분봉(900초) → 5분봉(300초) 변경 (288루프/일)
  - 5m 전략: 매 루프 평가, 15m 전략: 3루프마다 평가
  - 5m 레버리지: 보고서 권장값 적용 (10~20x, 노이즈 감안 보수적)
v5.1:
  [레버리지] WFA 보고서 레버리지 섹션 반영
  - 공식: recommended = floor(0.80 / (SL% + 0.4%))
  - leverage 값: L1=27, L2=14, L3=12, L4=33, L5=88
                  S1=27, S2=18, S3=18, S4=23, S5=23
  - max_leverage: theoretical_max 적용
  - _check_sl_above_liquidation SHORT 방향 지원 추가 (order_manager v2.17)
v5.0:
  [전략 교체] WFA OOS 보고서 기반 BTCUSDT 15m 전용 10개 전략으로 교체
  - 기존 17개 다심볼(BTC/ETH/XRP) → BTCUSDT 15m LONG 5 + SHORT 5
  - 충돌 해소: Sharpe → Score 기반 (WFA 종합 스코어)
  - entry_fn 아키텍처: 전략별 복합 진입 함수로 교체
  - 데이터 출처: BTCUSDT_15m_WFA_Report.docx (2026-03-21)
"""

import time
import traceback
from datetime import datetime, timezone

from config import LOOP_INTERVAL_SEC
from strategies.registry import STRATEGY_REGISTRY
from core.data_manager import get_balance, clear_cache
from core.signal_generator import generate_all_signals
from core.signal_arbiter import arbitrate
from core.position_manager import (
    get_open_positions, get_position_age_bars, record_position_timeframe
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
# 5m 전략 추가로 최소 타임프레임 5m 기준 루프
# 5m 전략 매 루프, 15m 전략 3번째 루프에 평가
CANDLE_TF_SEC = 5 * 60   # 기준: 5분봉 (300초)
CANDLE_OFFSET = 3         # 봉 마감 후 3초 뒤 실행 (데이터 확정 여유)

# [v2.12] 루프 간 포지션 상태 추적 (청산 감지용)
_prev_open_positions: dict = {}

# [v2.18] 중복 알림 방지 — 이미 알림 발송한 청산/진입 건 기록
# key 형식: "{symbol}:{strategy_id}"
_notified_closes: set = set()   # 청산 알림 발송 완료 목록
_notified_entries: set = set()  # 진입 알림 발송 완료 목록


def wait_for_candle_close() -> None:
    """
    [v5.2] 다음 5분봉 마감 후 CANDLE_OFFSET초에 맞춰 sleep.
    5분 정각(00, 05, 10, 15, ..., 55분)에 +3초 시점에 루프가 시작됨.
    15분봉(5분의 배수)은 자동으로 동기화됨.
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
    """단일 루프 실행"""
    global _prev_open_positions   # [v2.12] 루프 간 포지션 상태 추적
    candle_id_at_start = _current_candle_id()   # v2.7: 봉 경계 추적
    logger.info("=" * 60)
    logger.info("[LOOP] 루프 시작")

    # ── 1. 캐시 초기화 (루프당 1회) ──────────────────────────
    clear_cache()

    # ── 2. 잔고 조회 (total = 배분 기준, free = 진입 가능 체크용) ──
    balance_total, balance_free = get_balance()
    if balance_total <= 0:
        logger.warning("[LOOP] 잔고 0 또는 조회 실패 — 이번 루프 스킵")
        _update_prev_snapshot(open_positions={})  # [v2.18] 잔고 실패 시에도 스냅샷 갱신
        return
    logger.info(
        f"[LOOP] 잔고 | total=${balance_total:.2f} USDT (walletBalance) | "
        f"free=${balance_free:.2f} USDT (availableBalance)"
    )

    # ── 3. 현재 포지션 조회 ───────────────────────────────────
    open_positions = get_open_positions()
    logger.info(f"[LOOP] 보유 포지션: {list(open_positions.keys()) or '없음'}")

    # ── 3-1. [v2.12/v2.18] 청산 감지 — TP/SL Algo Order 체결 알림 ─
    # 이전 루프에 있던 포지션이 이번 루프에 없으면 Binance가 자동 청산한 것
    # [v2.18] _notified_closes로 중복 알림 완전 차단
    _force_closed_this_loop: set = set()  # 24봉 강제청산 심볼 (중복 알림 방지)
    for sym, prev_info in _prev_open_positions.items():
        if sym not in open_positions:
            strat_id   = prev_info.get("strategy_id", "UNKNOWN")
            close_key  = f"{sym}:{strat_id}"

            # [v2.18] 이미 알림 보낸 건이면 스킵 (중복 방지 핵심)
            if close_key in _notified_closes:
                logger.debug(f"[LOOP] {sym} 청산 알림 이미 발송됨 → 스킵")
                continue

            entry_time = prev_info.get("entry_time", 0)
            pnl        = fetch_realized_pnl(sym, entry_time)
            result_lbl = "✅ 익절" if pnl > 0 else "❌ 손절"
            notify_close(strat_id, sym, result_lbl, pnl)
            _notified_closes.add(close_key)  # [v2.18] 발송 기록
            logger.info(f"[LOOP] {sym} 청산 감지 (TP/SL) → 텔레그램 알림 (PnL={pnl:+.4f})")

    # ── 4. max_hold_bars 초과 포지션 강제 청산 ────────────────
    for symbol, pos_info in list(open_positions.items()):
        tf            = pos_info.get("timeframe", "1h")
        strategy_id   = pos_info.get("strategy_id", "UNKNOWN")
        bar_hours     = TF_BAR_HOURS.get(tf, 1.0)
        age_h         = get_position_age_bars(symbol)   # 파일 기반 entry_time 사용

        # [v2.14] 전략별 max_hold_bars 조회 (레지스트리에 없으면 48봉 기본값)
        strat = STRATEGY_REGISTRY.get(strategy_id, {})
        max_hold_bars = strat.get("max_hold_bars", 48)
        max_hours     = max_hold_bars * bar_hours

        if age_h > max_hours:
            logger.warning(
                f"[LOOP] {symbol} {age_h:.1f}h 초과 "
                f"(기준: {max_hours:.1f}h = {tf} {max_hold_bars}봉) → 강제 청산"
            )
            notify_circuit_breaker(
                "POSITION_TIMEOUT",
                f"{symbol} {age_h:.1f}h 초과 → {tf} {max_hold_bars}봉 기준 강제 청산 ({strategy_id})"
            )
            cancel_all_open_orders(symbol)          # 일반 + Algo Order 동시 취소
            pos_side = pos_info.get("side", "long")  # [v2.9] Binance에서 조회한 포지션 방향
            close_position_market(symbol, pos_side=pos_side)  # v2.15: 방향 전달

            # [v2.12] 강제청산 즉시 텔레그램 알림 (unrealized_pnl 기준)
            force_pnl   = float(pos_info.get("unrealized_pnl", 0.0))
            strat_id    = pos_info.get("strategy_id", "UNKNOWN")
            result_lbl  = "✅ 익절" if force_pnl > 0 else "❌ 손절"
            notify_close(strat_id, symbol, f"⏰ {max_hold_bars}봉 강제청산 ({result_lbl})", force_pnl)
            _notified_closes.add(f"{symbol}:{strat_id}")  # [v2.18] 강제청산도 발송 기록
            _force_closed_this_loop.add(symbol)  # 다음 루프 중복 방지용 마킹

    # ── 4-1. [v2.10] ATR 전략 TP/SL 매 봉 갱신 ──────────────
    # ATR 기반 전략은 매 봉(5m/15m/1h)마다 최신 ATR로 TP/SL 재계산 후 Algo Order 재등록
    # SL Ratchet: 손실 방향으로의 SL 이동 금지 (유리한 방향으로만 이동)
    open_positions_after_close = get_open_positions()  # 강제청산 이후 갱신된 포지션
    update_atr_tp_sl(open_positions_after_close)

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
        _update_prev_snapshot(open_positions)  # [v2.17] early return 전 스냅샷 갱신
        return

    logger.info(f"[LOOP] 신호 발생: {len(signals)}개")

    # ── 6. Arbiter 필터링 ─────────────────────────────────────
    executable = arbitrate(signals, balance_total, open_positions)
    logger.info(f"[LOOP] 실행 가능 신호: {len(executable)}개")

    if not executable:
        logger.info("[LOOP] 실행할 신호 없음")
        _update_prev_snapshot(open_positions)  # [v2.17] early return 전 스냅샷 갱신
        return

    # ── 7. Score 순 실행 (CB 발동 시 다음 신호 폴오버) ───────
    order_placed = False
    # [v2.9] 이번 루프에서 execute_order 호출한 심볼 추적
    # [v5.0] arbiter v5.0에서 Score 기반 심볼 중복 제거 후 넘어오지만
    #         2중 방어 유지 (arbiter→main 사이에 포지션 변경 가능성 대비)
    executed_symbols: set = set()

    for top_sig in executable:
        strategy    = top_sig["strategy"]
        symbol      = strategy["symbol"]
        strategy_id = strategy["id"]
        leverage    = strategy["leverage"]
        base_mdd    = strategy["base_mdd"]
        timeframe   = strategy["timeframe"]

        # [v2.9] 1심볼 2중 진입 완전 차단
        # execute_order 호출 후 실패(TP/SL 실패→긴급청산 실패 등)해도
        # 동일 심볼로 다시 시도하면 2중 포지션 위험 → 이번 루프에서 완전 금지
        if symbol in executed_symbols:
            logger.warning(
                f"[LOOP] ⚠️ 2중진입 차단: {strategy_id} | {symbol} "
                f"이번 루프에서 이미 execute_order 호출됨 → 스킵"
            )
            continue

        # ── v2.7: 봉 경계 체크 ────────────────────────────────
        # 에러 연쇄로 루프가 길어져 봉이 넘어간 경우 나머지 신호 포기
        # → 다음 봉에서 새로 생성된 신호로 진입 (old 신호로 새 봉 진입 방지)
        current_candle = _current_candle_id()
        if current_candle != candle_id_at_start:
            elapsed = (current_candle - candle_id_at_start) * CANDLE_TF_SEC
            logger.warning(
                f"[LOOP] ⏰ 봉 경계 초과 — {elapsed/60:.0f}분 경과, 봉 {current_candle - candle_id_at_start}개 지남 "
                f"→ {strategy_id} 이후 포기, 다음 봉 대기"
            )
            break

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
        update_strategy_mdd(strategy_id, balance_total, base_mdd)

        # ── 9-1. [v2.10] free 잔고 검증 (total 기준 마진 ≠ free 바닥) ──
        # total으로 마진 계산했지만 실제로 진입할 수 있는지 free 로 커버 확인
        required_margin = top_sig["margin"]
        if balance_free < required_margin:
            logger.warning(
                f"[LOOP] ⚠️ 여유잔고 부족 — {strategy_id} | "
                f"필요 마진 ${required_margin:.2f} > free ${balance_free:.2f} → 스킵"
            )
            continue

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

        executed_symbols.add(symbol)   # [v2.9] 호출 즉시 등록 (성공/실패 무관)
        success = execute_order(top_sig)

        if success:
            # ✅ 진입 성공 → 타임프레임 + 진입시각 + 전략ID 파일 기록 (24봉 청산용)
            record_position_timeframe(symbol, timeframe, strategy_id)  # v2.9: strategy_id 추가

            # [v2.18] 새 진입 시 해당 심볼의 알림 기록 클리어
            #         → 이 포지션이 나중에 청산되면 정상 알림 발송됨
            entry_key = f"{symbol}:{strategy_id}"
            _notified_closes.discard(entry_key)
            _notified_entries.discard(entry_key)

            direction_label = top_sig.get("direction", "long").upper()   # v2.11: 동적 방향

            # [v2.18] 진입 알림도 1회만 발송
            if entry_key not in _notified_entries:
                notify_entry(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    side=direction_label,
                    entry=entry,
                    tp=tp,
                    sl=sl,
                    leverage=top_sig["strategy"]["leverage"],
                    margin=top_sig["margin"],
                )
                _notified_entries.add(entry_key)
            logger.info(f"[LOOP] ✅ 주문 완료: {strategy_id} [{direction_label}]")
            order_placed = True
            # [v2.11] break 제거: 1심볼당 1포지션 허용, 루프 당 여러 심볼 진입 가능
            # (동일 심볼 중복은 executed_symbols set 으로 계속 차단)
        else:
            logger.error(f"[LOOP] ❌ 주문 실패: {strategy_id} → {symbol} 이번 루프 재시도 금지")

    if not order_placed:
        logger.info("[LOOP] 모든 신호 시도 완료 (주문 없음)")

    # ── [v2.17] 루프 끝: 현재 포지션 스냅샷 저장 ────────────────
    _update_prev_snapshot(open_positions, _force_closed_this_loop)


def _update_prev_snapshot(
    open_positions: dict,
    force_closed: set | None = None,
) -> None:
    """
    [v2.17] _prev_open_positions 스냅샷 갱신.
    청산 감지 직후 _prev에서 즉시 제거 + 루프 끝에 전체 갱신.
    """
    global _prev_open_positions
    snapshot = dict(open_positions)
    if force_closed:
        for sym in force_closed:
            snapshot.pop(sym, None)
    _prev_open_positions = snapshot


def main() -> None:
    logger.info("🚀 SMRA Bot v5.4 시작 (BTCUSDT 5m+15m+1h+4h WFA 40전략 + Score 충돌 해소 + WFA 레버리지)")
    logger.info(f"루프 간격: 5분봉 마감 동기화 (288루프/일) | 40개 전략 (5m:매 루프, 15m:3루프, 1h:12루프, 4h:48루프마다) | Score 순위 충돌 해소")

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
