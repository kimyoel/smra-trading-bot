"""
core/order_manager.py — ccxt futures 주문 발행 (v2.16)

버그 수정 히스토리:
  v2.13 : ccxt 4.5.43 + triggerPrice → /fapi/v1/algoOrder 자동 라우팅 (-4120 해결)
  v2.14 :
  [FIX1] cancel_all_open_orders(): 일반 주문 + Algo Order 동시 취소
  [FIX2] close_position_market(): Binance 실시간 포지션 크기 재조회
  [FIX3] SL/강제청산 가격 안전 체크 (_check_sl_above_liquidation)
  v2.15 :
  [FIX4] LONG/SHORT 양방향 지원 구조 추가
         - _place_algo_order(): direction 파라미터 추가
           LONG TP/SL → side="sell" (반대방향 청산)
           SHORT TP/SL → side="buy" (반대방향 청산)
         - _emergency_close(): direction 파라미터 추가
           LONG 긴급청산 → side="sell" / SHORT 긴급청산 → side="buy"
         - execute_order(): strategy의 direction 필드 읽기
           direction="long" (기본값): 기존 매수 진입
           direction="short": 매도 진입, TP/SL side 반전
         - close_position_market(): pos_side 파라미터 추가
  v2.16 :
  [FIX5] 실제 체결가 기반 TP/SL 재계산
         - MARKET 진입 직후 entry_order["average"] 사용
         - average가 None/0이면 fetch_order로 재조회 (최대 3회, 0.5초 간격)
         - 그래도 실패 시 signal entry_price fallback (로그에 경고)
         - 실제 체결가로 tp/sl 재계산 후 algo order 등록
         → 슬리피지로 인한 TP/SL 가격 오차 제거
           position_manager의 side 정보로 올바른 청산 방향 결정
         현재 모든 전략은 direction 미설정 → "long" 기본값 → 기존 동작 유지
         숏 전략 추가 시 registry에 "direction": "short" 추가하면 자동 작동
"""

import math
import ccxt
from config import MIN_NOTIONAL
from core.data_manager import exchange
from utils.logger import get_logger

logger = get_logger("order_manager")

# ── 심볼별 수량 precision (바이낸스 선물 기준) ───────────────
AMOUNT_PRECISION = {
    "BTC/USDT":  3,   # 0.001 단위
    "ETH/USDT":  3,   # 0.001 단위
    "XRP/USDT":  0,   # 1 단위 (정수)
}

# ── 심볼별 최소 수량 (바이낸스 선물 기준) ───────────────────
MIN_QTY = {
    "BTC/USDT":  0.001,
    "ETH/USDT":  0.001,
    "XRP/USDT":  1.0,
}

# ── 바이낸스 선물 유지증거금률 (Maintenance Margin Rate) ────
# LONG 포지션 강제청산 가격 ≈ entry × (1 - 1/leverage + MMR)
# SL이 이 가격보다 위에 있어야 강제청산 전에 SL 발동됨
BINANCE_MMR = {
    "BTC/USDT":  0.004,   # 0.4% (소규모 포지션 기준)
    "ETH/USDT":  0.005,   # 0.5%
    "XRP/USDT":  0.005,   # 0.5%
}


# ── 심볼 변환 ────────────────────────────────────────────────
def _to_raw_symbol(symbol: str) -> str:
    """'BTC/USDT' → 'BTCUSDT'"""
    return symbol.split(":")[0].replace("/", "")


def _round_amount(symbol: str, amount: float) -> float:
    """바이낸스 선물 precision에 맞게 수량 내림 처리"""
    precision = AMOUNT_PRECISION.get(symbol, 3)
    factor    = 10 ** precision
    return math.floor(amount * factor) / factor


def _ensure_min_notional(symbol: str, amount: float, entry: float) -> float:
    """
    floor 후 명목가치가 MIN_NOTIONAL 미달이면 한 단계 올림.
    부동소수점 오염 방지: round()로 최종 정리.
    """
    min_not   = MIN_NOTIONAL.get(symbol, 100.0)
    notional  = amount * entry
    precision = AMOUNT_PRECISION.get(symbol, 3)

    if notional < min_not:
        step   = 1 / (10 ** precision)
        bumped = round(amount + step, precision)
        bumped_notional = bumped * entry
        logger.info(
            f"[ORDER] 명목가치 조정: {amount} → {bumped} {symbol.split('/')[0]} "
            f"(${notional:.2f} → ${bumped_notional:.2f}, MIN=${min_not})"
        )
        return bumped

    return amount


def _check_sl_above_liquidation(
    symbol: str,
    entry: float,
    sl: float,
    leverage: int,
) -> None:
    """
    [v2.14] SL이 강제청산 가격보다 위에 있는지 검증.

    LONG 강제청산(Liquidation) 근사 가격:
        liq ≈ entry × (1 - 1/leverage + MMR)

    SL < liq 이면: 가격이 SL에 도달하기 전에 강제청산됨 → 위험!
    이 경우 경고 로그 출력 (주문 자체는 막지 않음, 전략 파라미터 문제이므로)

    레버리지와 TP/SL의 관계 정리:
        - TP/SL 가격은 항상 진입가 기준 '가격 이동 %'로 설정 (레버리지 무관)
        - 레버리지는 손익 배율(자본금 대비 수익률)에만 영향
        - 예: 10x 레버리지 + SL -0.5% → 자본금 -5% 손실 (적절한 리스크)
        - 단, SL이 강제청산 가격보다 낮으면 SL이 발동 안 됨 → 이 함수로 체크
    """
    mmr     = BINANCE_MMR.get(symbol, 0.005)
    liq_est = entry * (1 - 1 / leverage + mmr)

    sl_pct  = (sl - entry) / entry * 100   # 음수
    liq_pct = (liq_est - entry) / entry * 100   # 음수

    if sl < liq_est:
        logger.warning(
            f"[ORDER] ⚠️ SL 강제청산 우선 위험! {symbol} | "
            f"SL={sl:.4f} ({sl_pct:.2f}%) < LiqEst={liq_est:.4f} ({liq_pct:.2f}%) | "
            f"레버리지={leverage}x → SL 발동 전 강제청산될 수 있음"
        )
    else:
        logger.info(
            f"[ORDER] ✅ SL/Liq 안전 확인: {symbol} | "
            f"SL={sl:.4f} ({sl_pct:.2f}%) > LiqEst={liq_est:.4f} ({liq_pct:.2f}%) | "
            f"레버리지={leverage}x"
        )


def set_leverage(symbol: str, leverage: int) -> bool:
    """레버리지 설정"""
    try:
        exchange.set_leverage(leverage, symbol)
        logger.info(f"[ORDER] 레버리지 설정: {symbol} {leverage}x")
        return True
    except Exception as e:
        logger.error(f"[ORDER] 레버리지 설정 실패 {symbol}: {e}")
        return False


def _place_algo_order(
    symbol: str,
    order_type: str,
    stop_price: float,
    amount: float,
    direction: str = "long",   # [v2.15] "long" | "short"
) -> dict:
    """
    TP/SL 주문을 Binance Algo Order API로 전송 (v2.13+).

    2025-12-09 바이낸스 변경 후 TAKE_PROFIT_MARKET / STOP_MARKET은
    POST /fapi/v1/algoOrder 엔드포인트만 허용. ccxt 4.5.43+에서
    triggerPrice 파라미터 사용 시 자동으로 fapiPrivatePostAlgoOrder 라우팅.

    [v2.15] One-way 모드 방향별 side:
        LONG 포지션 청산 → side="sell" (TP/SL 모두)
        SHORT 포지션 청산 → side="buy"  (TP/SL 모두)
    """
    close_side = "sell" if direction == "long" else "buy"
    return exchange.create_order(
        symbol=symbol,
        type=order_type,
        side=close_side,
        amount=amount,
        price=None,
        params={
            "triggerPrice": str(round(stop_price, 2)),
            "workingType":  "MARK_PRICE",
            "timeInForce":  "GTE_GTC",
            "reduceOnly":   True,
        },
    )


def _emergency_close(symbol: str, amount: float, direction: str = "long") -> None:
    """
    TP/SL 등록 실패 시 긴급 시장가 청산. (v2.15: direction 파라미터 추가)
    무방어 포지션 방지용 안전장치.

    LONG 포지션 긴급청산 → side="sell"
    SHORT 포지션 긴급청산 → side="buy"
    """
    close_side = "sell" if direction == "long" else "buy"
    try:
        size = _round_amount(symbol, amount)
        if size <= 0:
            logger.warning(f"[ORDER] ⚠️ 긴급 청산 수량 0 — 스킵 (수동 확인 필요!)")
            return
        exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side=close_side,
            amount=size,
            params={"reduceOnly": True}
        )
        logger.warning(f"[ORDER] ⚠️ 긴급 청산 완료: {symbol} {size} dir={direction} (TP/SL 등록 실패 대응)")
    except Exception as e:
        logger.error(f"[ORDER] 긴급 청산 실패 {symbol}: {e} — 수동 확인 필요!")


def execute_order(sig: dict) -> bool:
    """
    진입 주문 + TP + SL 발행. (v2.15: LONG/SHORT 방향 지원)

    1. 레버리지 설정
    2. 수량 계산 (precision + min_qty + min_notional 체크)
    3. SL/강제청산 가격 안전 체크 (v2.14, LONG만)
    4. MARKET 진입 주문 (LONG=buy / SHORT=sell)
    5. TAKE_PROFIT_MARKET (→ /fapi/v1/algoOrder)
    6. STOP_MARKET        (→ /fapi/v1/algoOrder)
    * TP/SL 실패 시 → 즉시 긴급 청산 후 False 반환

    [v2.15] strategy에 direction 필드 추가로 숏 지원:
        direction="long"  (기본값): BUY 진입, SELL TP/SL
        direction="short": SELL 진입, BUY TP/SL
    현재 모든 전략은 direction 미설정 → "long" 기본값 → 기존 동작 완전 유지
    """
    strategy    = sig["strategy"]
    symbol      = strategy["symbol"]
    strategy_id = strategy["id"]
    leverage    = strategy["leverage"]
    margin      = sig["margin"]
    tp          = sig["tp"]
    sl          = sig["sl"]
    entry       = sig["entry_price"]

    # [v2.16] LONG/SHORT 방향: signal_generator가 설정한 sig["direction"] 우선,
    #          없으면 strategy 필드, 최종 폴백 "long"
    direction  = sig.get("direction") or strategy.get("direction", "long")
    direction  = direction.lower()
    entry_side = "buy"  if direction == "long" else "sell"
    dir_label  = "LONG" if direction == "long" else "SHORT"

    entry_order_id = None
    amount         = 0.0

    try:
        # 1. 레버리지 설정
        if not set_leverage(symbol, leverage):
            return False

        # 2. 포지션 수량 계산
        notional = margin * leverage
        amount   = _round_amount(symbol, notional / entry)

        min_qty = MIN_QTY.get(symbol, 0.001)
        if amount < min_qty:
            logger.warning(
                f"[ORDER] {strategy_id} 수량 {amount} < 최소 {min_qty} → 주문 취소\n"
                f"  마진=${margin:.2f}, 레버리지={leverage}x, 명목=${notional:.2f}, 가격={entry}"
            )
            return False

        amount = _ensure_min_notional(symbol, amount, entry)

        # 3. SL / 강제청산 가격 안전 체크 (LONG만: SHORT는 반대 방향 공식 필요)
        if direction == "long":
            _check_sl_above_liquidation(symbol, entry, sl, leverage)

        logger.info(
            f"[ORDER] 진입 시도 | {strategy_id} | {symbol} {dir_label} | "
            f"수량: {amount} | 마진: ${margin:.2f} | {leverage}x | "
            f"TP: {tp:.4f} ({(tp/entry-1)*100:+.2f}%) | "
            f"SL: {sl:.4f} ({(sl/entry-1)*100:+.2f}%) | "
            f"자본기준 TP: {(tp/entry-1)*100*leverage:+.1f}% / SL: {(sl/entry-1)*100*leverage:+.1f}%"
        )

        # 4. MARKET 진입 주문
        entry_order = exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side=entry_side,   # LONG=buy / SHORT=sell
            amount=amount,
        )
        entry_order_id = entry_order.get("id", "N/A")
        logger.info(f"[ORDER] 진입 주문 체결: {entry_order_id} ({dir_label})")

        # [v2.16] 실제 체결가 확인 후 TP/SL 재계산
        # MARKET 주문은 즉시 체결되지만 average 필드가 None일 수 있어 재조회
        import time as _time
        fill_price = entry_order.get("average") or entry_order.get("price")
        if not fill_price or float(fill_price) <= 0:
            for _retry in range(3):
                _time.sleep(0.5)
                try:
                    fetched = exchange.fetch_order(entry_order_id, symbol)
                    fill_price = fetched.get("average") or fetched.get("price")
                    if fill_price and float(fill_price) > 0:
                        logger.info(f"[ORDER] 체결가 재조회 성공 ({_retry+1}회): {fill_price}")
                        break
                except Exception as _fe:
                    logger.warning(f"[ORDER] fetch_order 재시도 {_retry+1}/3 실패: {_fe}")
        if fill_price and float(fill_price) > 0:
            fill_price = float(fill_price)
            # 전략 TP/SL 비율 그대로 실제 체결가에 적용
            strat = sig["strategy"]
            tp_type  = strat.get("tp_type", "fixed")
            tp_mult  = strat.get("tp_mult", 0.01)
            sl_mult  = strat.get("sl_mult", 0.005)
            atr_val  = sig.get("atr", None)
            if tp_type == "atr" and atr_val and float(atr_val) > 0:
                if direction == "long":
                    tp = fill_price + float(atr_val) * tp_mult
                    sl = fill_price - float(atr_val) * sl_mult
                else:
                    tp = fill_price - float(atr_val) * tp_mult
                    sl = fill_price + float(atr_val) * sl_mult
            else:
                if direction == "long":
                    tp = fill_price * (1 + tp_mult)
                    sl = fill_price * (1 - sl_mult)
                else:
                    tp = fill_price * (1 - tp_mult)
                    sl = fill_price * (1 + sl_mult)
            logger.info(
                f"[ORDER] 체결가 기반 TP/SL 재계산 완료 | fill={fill_price:.4f} "
                f"(signal={entry:.4f}, 슬리피지={abs(fill_price-entry)/entry*100:.3f}%) | "
                f"TP={tp:.4f} ({(tp/fill_price-1)*100:+.2f}%) SL={sl:.4f} ({(sl/fill_price-1)*100:+.2f}%)"
            )
        else:
            logger.warning(
                f"[ORDER] 실제 체결가 조회 실패 → signal entry_price({entry:.4f}) fallback 사용"
            )

        # 5. TAKE_PROFIT_MARKET — Algo Order API (v2.13+)
        try:
            tp_resp = _place_algo_order(symbol, "TAKE_PROFIT_MARKET", tp, amount, direction)
            tp_id   = tp_resp.get("id", tp_resp.get("algoId", "N/A"))
            logger.info(f"[ORDER] TP algoOrder 등록: {tp_id} @ {tp:.4f}")
        except Exception as e:
            logger.error(f"[ORDER] TP 등록 실패 → 긴급 청산 실행: {e}")
            _emergency_close(symbol, amount, direction)
            return False

        # 6. STOP_MARKET — Algo Order API (v2.13+)
        try:
            sl_resp = _place_algo_order(symbol, "STOP_MARKET", sl, amount, direction)
            sl_id   = sl_resp.get("id", sl_resp.get("algoId", "N/A"))
            logger.info(f"[ORDER] SL algoOrder 등록: {sl_id} @ {sl:.4f}")
        except Exception as e:
            logger.error(f"[ORDER] SL 등록 실패 → 긴급 청산 실행: {e}")
            _emergency_close(symbol, amount, direction)
            return False

        return True

    except ccxt.InsufficientFunds as e:
        logger.error(f"[ORDER] 잔고 부족 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount, direction)
        return False
    except ccxt.InvalidOrder as e:
        logger.error(f"[ORDER] 잘못된 주문 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount, direction)
        return False
    except ccxt.ExchangeError as e:
        logger.error(f"[ORDER] 거래소 오류 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount, direction)
        return False
    except Exception as e:
        logger.error(f"[ORDER] 알 수 없는 오류 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount, direction)
        return False


def cancel_all_open_orders(symbol: str) -> None:
    """
    해당 심볼 미체결 주문 전부 취소 (v2.14: 일반 주문 + Algo Order 동시).

    2025-12-09 이후 TP/SL이 Algo Order로 전환됨.
    기존 cancel_all_orders()는 /fapi/v1/allOpenOrders만 취소하므로
    Algo Order(/fapi/v1/algoOpenOrders)는 잔존 → 좀비 주문 발생 가능.
    → 일반 주문 취소 + fapiPrivateDeleteAlgoOpenOrders 모두 호출.
    """
    raw = _to_raw_symbol(symbol)

    # ① 일반 미체결 주문 취소
    try:
        exchange.cancel_all_orders(symbol)
        logger.info(f"[ORDER] {symbol} 일반 미체결 주문 전부 취소")
    except Exception as e:
        logger.error(f"[ORDER] 일반 주문 취소 실패 {symbol}: {e}")

    # ② Algo Order 취소 (TP/SL은 algoOpenOrders에 있음)
    try:
        exchange.fapiPrivateDeleteAlgoOpenOrders({"symbol": raw})
        logger.info(f"[ORDER] {symbol} Algo 미체결 주문 전부 취소 (TP/SL)")
    except Exception as e:
        # 열린 algoOrder가 없으면 에러가 날 수 있음 — 경고 수준으로 처리
        logger.warning(f"[ORDER] Algo 주문 취소 실패 (없을 수도 있음) {symbol}: {e}")


def close_position_market(symbol: str, size: float = 0.0, pos_side: str = "long") -> None:
    """
    시장가 강제 청산 (v2.15: pos_side 파라미터 추가 → LONG/SHORT 올바른 방향 청산).

    기존: 외부에서 넘겨받은 size 사용 → 부분 청산, 누락 등으로 불일치 가능
    v2.14: Binance fetch_positions()로 실시간 포지션 크기 조회 후 사용
    v2.15: pos_side로 청산 방향 결정
           LONG 포지션 청산 → side="sell"
           SHORT 포지션 청산 → side="buy"
    """
    # Binance 실시간 포지션 크기 재조회
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos.get("contracts", 0) or 0)
            if contracts > 0:
                raw_size = contracts
                # symbol 정규화 비교
                pos_sym = pos["symbol"].split(":")[0]
                if pos_sym == symbol.split(":")[0]:
                    size = raw_size
                    logger.info(
                        f"[ORDER] 강제청산 실시간 수량 확인: {symbol} → {size} "
                        f"(Binance fetch_positions)"
                    )
                    break
    except Exception as e:
        logger.warning(
            f"[ORDER] 강제청산 실시간 조회 실패 — 파라미터 size({size}) 폴백: {e}"
        )

    close_side = "sell" if pos_side == "long" else "buy"   # [v2.15]
    size = _round_amount(symbol, size)
    if size <= 0:
        logger.warning(f"[ORDER] {symbol} 강제청산 수량 0 → 스킵")
        return

    try:
        exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side=close_side,
            amount=size,
            params={"reduceOnly": True}
        )
        logger.info(f"[ORDER] {symbol} 강제 청산 완료 (size={size}, side={close_side})")
    except Exception as e:
        logger.error(f"[ORDER] 강제 청산 실패 {symbol}: {e}")
