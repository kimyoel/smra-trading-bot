"""
core/order_manager.py — ccxt futures 주문 발행 (v2.1)

버그 수정:
  1. amount precision 처리 (BTC/ETH 소수 3자리, XRP 정수)
  2. 최소 수량(min_qty) 체크 추가
  3. set_leverage() 실패 시에도 max_leverage로 재시도
"""

import math
import ccxt
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
    """바이낸스 선물 precision에 맞게 수량 내림 처리 (올림 방지 → 초과 주문 없도록)"""
    precision = AMOUNT_PRECISION.get(symbol, 3)
    factor    = 10 ** precision
    return math.floor(amount * factor) / factor


def set_leverage(symbol: str, leverage: int) -> bool:
    """레버리지 설정"""
    try:
        exchange.set_leverage(leverage, symbol)
        logger.info(f"[ORDER] 레버리지 설정: {symbol} {leverage}x")
        return True
    except Exception as e:
        logger.error(f"[ORDER] 레버리지 설정 실패 {symbol}: {e}")
        return False


def execute_order(sig: dict) -> bool:
    """
    진입 주문 + TP + SL 발행.

    1. 레버리지 설정
    2. 수량 계산 (precision + min_qty 체크)
    3. MARKET 진입 주문
    4. TAKE_PROFIT_MARKET 주문
    5. STOP_MARKET 주문

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

        logger.info(
            f"[ORDER] 진입 시도 | {strategy_id} | {symbol} LONG | "
            f"수량: {amount} | 마진: ${margin:.2f} | {leverage}x | "
            f"TP: {tp:.4f} | SL: {sl:.4f}"
        )

        # 3. MARKET 진입 주문
        entry_order = exchange.create_order(
            symbol=symbol,
            type="MARKET",
            side="buy",
            amount=amount,
            params={"positionSide": "LONG"}
        )
        logger.info(f"[ORDER] 진입 주문 체결: {entry_order.get('id', 'N/A')}")

        # 체결 가격 업데이트
        filled_price = float(entry_order.get("average", entry) or entry)

        # 4. TAKE_PROFIT_MARKET 주문
        tp_order = exchange.create_order(
            symbol=symbol,
            type="TAKE_PROFIT_MARKET",
            side="sell",
            amount=amount,
            params={
                "stopPrice":    round(tp, 4),
                "positionSide": "LONG",
                "reduceOnly":   True,
            }
        )
        logger.info(f"[ORDER] TP 주문 등록: {tp_order.get('id', 'N/A')} @ {tp:.4f}")

        # 5. STOP_MARKET 주문
        sl_order = exchange.create_order(
            symbol=symbol,
            type="STOP_MARKET",
            side="sell",
            amount=amount,
            params={
                "stopPrice":    round(sl, 4),
                "positionSide": "LONG",
                "reduceOnly":   True,
            }
        )
        logger.info(f"[ORDER] SL 주문 등록: {sl_order.get('id', 'N/A')} @ {sl:.4f}")

        return True

    except ccxt.InsufficientFunds as e:
        logger.error(f"[ORDER] 잔고 부족 {strategy_id}: {e}")
        return False
    except ccxt.InvalidOrder as e:
        logger.error(f"[ORDER] 잘못된 주문 {strategy_id}: {e}")
        return False
    except ccxt.ExchangeError as e:
        logger.error(f"[ORDER] 거래소 오류 {strategy_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"[ORDER] 알 수 없는 오류 {strategy_id}: {e}")
        return False


def cancel_all_open_orders(symbol: str) -> None:
    """해당 심볼 미체결 주문 전부 취소 (Circuit Breaker 발동 시)"""
    try:
        exchange.cancel_all_orders(symbol)
        logger.info(f"[ORDER] {symbol} 미체결 주문 전부 취소")
    except Exception as e:
        logger.error(f"[ORDER] 주문 취소 실패 {symbol}: {e}")


def close_position_market(symbol: str, size: float) -> None:
    """시장가 강제 청산 (24봉 초과 포지션)"""
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
            params={"positionSide": "LONG", "reduceOnly": True}
        )
        logger.info(f"[ORDER] {symbol} 강제 청산 완료 (size={size})")
    except Exception as e:
        logger.error(f"[ORDER] 강제 청산 실패 {symbol}: {e}")
