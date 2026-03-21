"""
core/signal_arbiter.py — 필터링 + 타임프레임×Score 정렬 + 충돌 해소 (v6.0.1 Hedge Mode)

[v6.0.1] 방향별 15% 자본배분 적용
  - CAPITAL_ALLOCATION 키: (symbol, direction) 튜플 형식으로 변경
  - LONG 15% + SHORT 15% = 심볼당 최대 30% (기존 60% 과다 노출 방지)

[v6.0] 헤지 모드 충돌 해소 전면 전환
  - 동일 심볼에 LONG + SHORT 동시 진입 허용
  - 충돌 해소 키: symbol → (symbol, direction) 복합 키
  - 동일 심볼 + 동일 방향 복수 신호 → 가장 큰 TF의 최고 Score 1개만
  - 동일 심볼 + 반대 방향은 독립 실행 (LONG 1 + SHORT 1)
  - 포지션 중복 필터: open_positions 키가 "symbol:LONG"/"symbol:SHORT"

[v5.3] 타임프레임 우선순위 기반 충돌 해소
  - 1차 기준: 큰 타임프레임 우선 (1h > 15m > 5m)
  - 2차 기준: 동일 타임프레임 내 WFA Score 내림차순

변경사항:
  v6.0.1: 방향별 15% 자본배분 (CAPITAL_ALLOCATION 키 변경)
  v6.0: Hedge Mode — (symbol, direction) 단위 충돌 해소
  v5.3: Score → 타임프레임 1차 + Score 2차, 큰 봉 우선
  v5.0: Sharpe → Score, 단일 심볼 최적화, 보고서 순위 반영
"""

from config import MIN_NOTIONAL, CAPITAL_ALLOCATION
from core.position_manager import make_pos_key
from utils.logger import get_logger

logger = get_logger("signal_arbiter")

# ── 타임프레임 우선순위 (큰 봉일수록 높은 가중치) ──────────────────
# 충돌 해소 시 1차 정렬 기준: 높을수록 우선
TF_PRIORITY = {
    "4h": 400,
    "1h": 300,
    "15m": 200,
    "5m": 100,
}

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
    신호 필터링 후 타임프레임×Score 정렬된 실행 가능 신호 반환. (v5.3)

    [v5.3 변경점]
      - 1차: 큰 타임프레임 우선 (1h > 15m > 5m)
      - 2차: 동일 타임프레임 내 Score 내림차순
      - 동일 심볼 복수 신호 → 가장 큰 TF의 최고 Score 1개만 실행
      - 이유: 큰 봉은 노이즈 적고, WFA 생존윈도우 넓어 신뢰도 높음

    Args:
        signals:        generate_all_signals() 반환값
        balance:        현재 사용 가능 USDT (free balance)
        open_positions: {symbol: position_info} 현재 보유 포지션

    Returns:
        실행 가능한 신호 리스트 (타임프레임 우선, Score 내림차순)
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

        # ── 필터 1: 심볼+방향 포지션 중복 (v6.0 Hedge Mode) ────
        # 동일 심볼이라도 반대 방향은 허용 (LONG + SHORT 독립)
        direction = sig.get("direction", "long")
        pos_key  = make_pos_key(symbol, direction)
        if pos_key in open_positions:
            logger.info(f"[ARBITER] SKIP-POS | {strategy_id} — {pos_key} 포지션 보유 중")
            continue

        # ── 필터 2: 최소 명목가치 (v6.0.1: 방향별 자본배분) ───
        alloc    = CAPITAL_ALLOCATION.get((symbol, direction), 0)
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

    # ── [v6.0] 타임프레임 우선 + Score 기반 (symbol, direction) 충돌 해소 ──
    # 헤지 모드: 동일 심볼이라도 LONG/SHORT 독립 허용
    # 충돌 해소 키: (symbol, direction) — 같은 심볼+방향 복수 → 큰 TF 최고 Score 1개
    executable.sort(
        key=lambda x: (
            TF_PRIORITY.get(x["strategy"]["timeframe"], 0),
            x["score"],
        ),
        reverse=True,
    )

    seen_sym_dir: dict = {}  # {(symbol, direction): (strategy_id, tf)}
    deduplicated = []

    for sig in executable:
        symbol      = sig["strategy"]["symbol"]
        strategy_id = sig["strategy"]["id"]
        score       = sig["score"]
        direction   = sig["direction"]

        tf          = sig["strategy"]["timeframe"]
        conflict_key = (symbol, direction)

        if conflict_key in seen_sym_dir:
            winner_id, winner_tf = seen_sym_dir[conflict_key]
            logger.info(
                f"[ARBITER] SKIP-TF-CONFLICT | {strategy_id} ({tf}, {direction.upper()}, Score {score:.2f}) — "
                f"{symbol} [{direction.upper()}] 이미 {winner_id} ({winner_tf}) 선택됨"
            )
            continue

        seen_sym_dir[conflict_key] = (strategy_id, tf)
        deduplicated.append(sig)

    if deduplicated:
        logger.info(
            f"[ARBITER] 🏆 최종 실행 신호 {len(deduplicated)}개 "
            f"(헤지 모드 — 심볼+방향별 충돌 해소 후):"
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
