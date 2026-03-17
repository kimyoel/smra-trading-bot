"""
core/risk_manager.py — Circuit Breaker (시스템 이상 감지 전용)
감정 기반 손절 로직 없음. 시스템/시장 이상만 감지.
"""

import time
from config import (
    CB_MAX_API_ERRORS, CB_FLASH_CRASH_PCT, CB_FLASH_PAUSE_SEC,
    CB_SPREAD_MAX, CB_FUNDING_MAX, CB_MDD_MULTIPLIER
)
from core.data_manager import fetch_ohlcv, fetch_funding_rate, fetch_orderbook
from utils.logger import get_logger
from utils.notifier import notify_circuit_breaker

logger = get_logger("risk_manager")

# ── 상태 추적 ────────────────────────────────────────────────
_api_error_count:  int   = 0
_flash_pause_until: dict = {}   # {symbol: timestamp}
_paused_strategies: set  = set()
_strategy_peak_balance: dict = {}  # {strategy_id: peak}
_strategy_drawdown: dict     = {}  # {strategy_id: current_mdd}


def increment_api_error() -> int:
    global _api_error_count
    _api_error_count += 1
    return _api_error_count


def reset_api_error() -> None:
    global _api_error_count
    _api_error_count = 0


def check_circuit_breaker(symbol: str, strategy_id: str,
                           strategy_base_mdd: float) -> dict:
    """
    Circuit Breaker 전체 체크.
    반환: {"block": bool, "reason": str, "action": str}
    """

    # ── 1. API 연속 오류 ──────────────────────────────────────
    if _api_error_count >= CB_MAX_API_ERRORS:
        logger.warning(f"[CB] API 오류 누적 {_api_error_count}회 → 대기")
        notify_circuit_breaker("API_ERROR_FLOOD", f"연속 {_api_error_count}회 오류")
        return {"block": True, "reason": "API_ERROR_FLOOD", "action": "WAIT_60S"}

    # ── 2. 플래시 크래시 감지 ──────────────────────────────────
    now = time.time()
    if symbol in _flash_pause_until and now < _flash_pause_until[symbol]:
        remaining = int(_flash_pause_until[symbol] - now)
        logger.info(f"[CB] {symbol} 플래시 크래시 대기 중 ({remaining}초 남음)")
        return {"block": True, "reason": "FLASH_CRASH_PAUSE", "action": f"WAIT_{remaining}S"}

    df_15m = fetch_ohlcv(symbol, "15m", limit=20)
    if df_15m is not None and len(df_15m) >= 16:
        current_price  = float(df_15m["close"].iloc[-1])
        price_15m_ago  = float(df_15m["close"].iloc[-16])
        drop = (current_price - price_15m_ago) / price_15m_ago
        if drop < CB_FLASH_CRASH_PCT:
            _flash_pause_until[symbol] = now + CB_FLASH_PAUSE_SEC
            msg = f"{symbol} 15분 {drop:.2%} 급락"
            logger.warning(f"[CB] 플래시 크래시 감지: {msg}")
            notify_circuit_breaker("FLASH_CRASH", msg)
            return {"block": True, "reason": "FLASH_CRASH", "action": "PAUSE_30M"}

    # ── 3. 스프레드 폭등 (유동성 붕괴) ───────────────────────
    ob = fetch_orderbook(symbol)
    if ob and ob.get("asks") and ob.get("bids"):
        ask = float(ob["asks"][0][0])
        bid = float(ob["bids"][0][0])
        mid = (ask + bid) / 2
        spread = (ask - bid) / mid if mid > 0 else 0
        if spread > CB_SPREAD_MAX:
            logger.info(f"[CB] {symbol} 스프레드 {spread:.4%} > {CB_SPREAD_MAX:.4%} → 스킵")
            return {"block": True, "reason": "HIGH_SPREAD", "action": "SKIP_CANDLE"}

    # ── 4. 펀딩비 급등 (block 아님, 레버리지만 감소) ─────────
    funding = fetch_funding_rate(symbol)
    if abs(funding) > CB_FUNDING_MAX:
        logger.info(f"[CB] {symbol} 펀딩비 {funding:.4%} 높음 → 레버리지 50% 감소 권고")
        return {
            "block":  False,
            "reason": "HIGH_FUNDING",
            "action": "REDUCE_LEVERAGE_50PCT",
            "funding_rate": funding,
        }

    # ── 5. 전략별 MDD 초과 감지 ───────────────────────────────
    if strategy_id in _paused_strategies:
        logger.info(f"[CB] {strategy_id} MDD 초과로 일시 중단 중")
        return {"block": True, "reason": "STRATEGY_MDD_EXCEEDED", "action": "STRATEGY_PAUSED"}

    return {"block": False, "reason": "", "action": ""}


def update_strategy_mdd(strategy_id: str, current_balance: float,
                         base_mdd: float) -> None:
    """
    전략별 MDD 추적.
    실거래 MDD가 백테스트 MDD × CB_MDD_MULTIPLIER 초과 시 전략 중단.
    """
    if strategy_id not in _strategy_peak_balance:
        _strategy_peak_balance[strategy_id] = current_balance

    peak = _strategy_peak_balance[strategy_id]
    if current_balance > peak:
        _strategy_peak_balance[strategy_id] = current_balance
        peak = current_balance

    if peak > 0:
        mdd = (peak - current_balance) / peak
        _strategy_drawdown[strategy_id] = mdd

        threshold = base_mdd * CB_MDD_MULTIPLIER
        if mdd > threshold and strategy_id not in _paused_strategies:
            _paused_strategies.add(strategy_id)
            msg = f"{strategy_id} MDD {mdd:.2%} > 임계값 {threshold:.2%}"
            logger.warning(f"[CB] 전략 중단: {msg}")
            notify_circuit_breaker("STRATEGY_MDD_EXCEEDED", msg)


def resume_strategy(strategy_id: str) -> None:
    """전략 수동 재개 (텔레그램 확인 후 수동 호출용)"""
    _paused_strategies.discard(strategy_id)
    logger.info(f"[CB] {strategy_id} 전략 재개")
