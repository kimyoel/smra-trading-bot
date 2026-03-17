"""
core/order_manager.py — ccxt futures 주문 발행 (v2.13)

버그 수정 히스토리:
  v2.1  : amount precision, min_qty, set_leverage 재시도
  v2.10 : positionSide 제거(단방향모드 -4061), 명목가치 자동 보정(-4164)
  v2.11 : [미배포] closePosition=True 시도 (amount=0 방식) → 실패
  v2.12 : fapiPrivatePostOrder 직접 호출 시도 → 여전히 -4120
           (POST /fapi/v1/order 자체가 2025-12-09 이후 조건부 주문 차단됨)
  v2.13 :
  [FIX1] -4120 완전 해결: ccxt 4.5.43 + create_order(triggerPrice=...) 방식
         2025-12-09 바이낸스 변경으로 TAKE_PROFIT_MARKET/STOP_MARKET은
         반드시 POST /fapi/v1/algoOrder 엔드포인트를 사용해야 함.
         ccxt 4.5.43에서 triggerPrice/stopLossPrice/takeProfitPrice 파라미터를
         넘기면 자동으로 fapiPrivatePostAlgoOrder(algoType=CONDITIONAL)로 라우팅됨.
  [FIX2] TP/SL 실패 시 즉시 긴급 시장가 청산 + 로깅 강화 (무방어 포지션 방지)
  [FIX3] 부동소수점 보정: round() 처리 유지
  [REQ]  requirements.txt: ccxt==4.5.43 필수
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
) -> dict:
    """
    TP/SL 주문을 Binance Algo Order API로 전송 (v2.13 핵심 수정).

    2025-12-09 바이낸스 변경 후 TAKE_PROFIT_MARKET / STOP_MARKET은
    POST /fapi/v1/order가 아닌 POST /fapi/v1/algoOrder 엔드포인트만 허용.
    ccxt 4.5.43+에서 triggerPrice 파라미터를 사용하면 자동으로
    fapiPrivatePostAlgoOrder(algoType=CONDITIONAL)로 라우팅됨.

    Args:
        symbol:     ccxt unified symbol (e.g. 'BTC/USDT')
        order_type: 'TAKE_PROFIT_MARKET' | 'STOP_MARKET'
        stop_price: trigger price (float)
        amount:     포지션 수량 (closePosition=true 동작을 위해 실제 수량 전달)
    """
    return exchange.create_order(
        symbol=symbol,
        type=order_type,
        side="sell",           # LONG 청산
        amount=amount,
        price=None,
        params={
            "triggerPrice":  str(round(stop_price, 2)),
            "workingType":   "MARK_PRICE",
            "timeInForce":   "GTE_GTC",
            "reduceOnly":    True,
        },
    )


def _emergency_close(symbol: str, amount: float) -> None:
    """
    TP/SL 등록 실패 시 긴급 시장가 청산 (v2.12+).
    무방어 포지션 방지용 안전장치.
    """
    try:
        size = _round_amount(symbol, amount)
        if size <= 0:
            logger.warning(f"[ORDER] ⚠️ 긴급 청산 수량 0 — 스킵 (수동 확인 필요!)")
            return
        exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side="sell",
            amount=size,
            params={"reduceOnly": True}
        )
        logger.warning(f"[ORDER] ⚠️ 긴급 청산 완료: {symbol} {size} (TP/SL 등록 실패 대응)")
    except Exception as e:
        logger.error(f"[ORDER] 긴급 청산 실패 {symbol}: {e} — 수동 확인 필요!")


def execute_order(sig: dict) -> bool:
    """
    진입 주문 + TP + SL 발행.

    1. 레버리지 설정
    2. 수량 계산 (precision + min_qty + min_notional 체크)
    3. MARKET 진입 주문
    4. TAKE_PROFIT_MARKET (ccxt → /fapi/v1/algoOrder, algoType=CONDITIONAL)
    5. STOP_MARKET        (ccxt → /fapi/v1/algoOrder, algoType=CONDITIONAL)
    * TP/SL 실패 시 → 즉시 긴급 청산 후 False 반환

    반환: 성공 True / 실패 False
    """
    strategy    = sig["strategy"]
    symbol      = strategy["symbol"]
    strategy_id = strategy["id"]
    leverage    = strategy["leverage"]
    margin      = sig["margin"]
    tp          = sig["tp"]
    sl          = sig["sl"]
    entry       = sig["entry_price"]

    entry_order_id = None   # 진입 성공 여부 추적
    amount         = 0.0    # 긴급 청산에서 참조 가능하도록 초기화

    try:
        # 1. 레버리지 설정
        if not set_leverage(symbol, leverage):
            return False

        # 2. 포지션 수량 계산
        notional = margin * leverage
        amount   = _round_amount(symbol, notional / entry)

        # 최소 수량 체크
        min_qty = MIN_QTY.get(symbol, 0.001)
        if amount < min_qty:
            logger.warning(
                f"[ORDER] {strategy_id} 수량 {amount} < 최소 {min_qty} → 주문 취소\n"
                f"  마진=${margin:.2f}, 레버리지={leverage}x, 명목=${notional:.2f}, 가격={entry}"
            )
            return False

        # 명목가치 MIN_NOTIONAL 미달 시 한 단계 올림
        amount = _ensure_min_notional(symbol, amount, entry)

        logger.info(
            f"[ORDER] 진입 시도 | {strategy_id} | {symbol} LONG | "
            f"수량: {amount} | 마진: ${margin:.2f} | {leverage}x | "
            f"TP: {tp:.4f} | SL: {sl:.4f}"
        )

        # 3. MARKET 진입 주문 (단방향 모드 — positionSide 없음)
        entry_order = exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side="buy",
            amount=amount,
        )
        entry_order_id = entry_order.get("id", "N/A")
        logger.info(f"[ORDER] 진입 주문 체결: {entry_order_id}")

        # 4. TAKE_PROFIT_MARKET — Algo Order API (v2.13, ccxt 4.5.43+)
        #    triggerPrice 파라미터 → 자동으로 /fapi/v1/algoOrder 라우팅
        try:
            tp_resp = _place_algo_order(symbol, "TAKE_PROFIT_MARKET", tp, amount)
            tp_id   = tp_resp.get("id", tp_resp.get("algoId", "N/A"))
            logger.info(f"[ORDER] TP 주문 등록 (algoOrder): {tp_id} @ {tp:.4f}")
        except Exception as e:
            logger.error(f"[ORDER] TP 등록 실패 → 긴급 청산 실행: {e}")
            _emergency_close(symbol, amount)
            return False

        # 5. STOP_MARKET — Algo Order API (v2.13, ccxt 4.5.43+)
        try:
            sl_resp = _place_algo_order(symbol, "STOP_MARKET", sl, amount)
            sl_id   = sl_resp.get("id", sl_resp.get("algoId", "N/A"))
            logger.info(f"[ORDER] SL 주문 등록 (algoOrder): {sl_id} @ {sl:.4f}")
        except Exception as e:
            logger.error(f"[ORDER] SL 등록 실패 → 긴급 청산 실행: {e}")
            _emergency_close(symbol, amount)
            return False

        return True

    except ccxt.InsufficientFunds as e:
        logger.error(f"[ORDER] 잔고 부족 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount)
        return False
    except ccxt.InvalidOrder as e:
        logger.error(f"[ORDER] 잘못된 주문 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount)
        return False
    except ccxt.ExchangeError as e:
        logger.error(f"[ORDER] 거래소 오류 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount)
        return False
    except Exception as e:
        logger.error(f"[ORDER] 알 수 없는 오류 {strategy_id}: {e}")
        if entry_order_id:
            _emergency_close(symbol, amount)
        return False


def cancel_all_open_orders(symbol: str) -> None:
    """해당 심볼 미체결 주문 전부 취소 (Circuit Breaker 발동 시)"""
    try:
        exchange.cancel_all_orders(symbol)
        logger.info(f"[ORDER] {symbol} 미체결 주문 전부 취소")
    except Exception as e:
        logger.error(f"[ORDER] 주문 취소 실패 {symbol}: {e}")


def close_position_market(symbol: str, size: float) -> None:
    """시장가 강제 청산 (2시간 초과 포지션)"""
    size = _round_amount(symbol, size)
    if size <= 0:
        logger.warning(f"[ORDER] {symbol} 청산 수량 0 → 스킵")
        return
    try:
        exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side="sell",
            amount=size,
            params={"reduceOnly": True}
        )
        logger.info(f"[ORDER] {symbol} 강제 청산 완료 (size={size})")
    except Exception as e:
        logger.error(f"[ORDER] 강제 청산 실패 {symbol}: {e}")
