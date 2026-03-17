"""
core/position_manager.py — 심볼당 1포지션 상태 추적 (v2.1)

수정:
  - get_position_age_bars() 함수 추가 (main.py에서 호출)
    get_position_age_hours()의 alias로 동작 (hours 단위 반환)
  - position_info에 timeframe 필드 추가
    (main.py의 TF_HOURS 매핑에 필요)
"""

import time
import ccxt
from core.data_manager import exchange
from utils.logger import get_logger

logger = get_logger("position_manager")

# strategy_id별 진입 시 타임프레임 기록
# get_open_positions()는 바이낸스 API에서 직접 조회하므로
# TF 정보는 별도로 in-memory 관리 (Railway 재시작 시 1h 기본값 사용)
_position_timeframe: dict = {}  # {symbol: timeframe}


def record_position_timeframe(symbol: str, timeframe: str) -> None:
    """진입 시 타임프레임 기록 (order_manager 또는 main에서 호출)"""
    _position_timeframe[symbol] = timeframe


def get_open_positions() -> dict:
    """
    현재 열린 포지션 조회.
    반환: {symbol: position_info}
    예: {"BTC/USDT": {"side": "long", "size": 0.001, "entry": 85000.0, "timeframe": "15m"}}
    """
    try:
        positions = exchange.fetch_positions()
        result = {}
        for pos in positions:
            size = float(pos.get("contracts", 0) or 0)
            if size == 0:
                continue
            symbol = pos["symbol"]
            result[symbol] = {
                "side":           pos.get("side", "long"),
                "size":           size,
                "entry":          float(pos.get("entryPrice", 0) or 0),
                "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
                "timestamp":      pos.get("timestamp", 0),
                # 타임프레임: 진입 시 기록된 값, 없으면 "1h" 기본
                "timeframe":      _position_timeframe.get(symbol, "1h"),
            }
        return result
    except Exception as e:
        logger.error(f"[POSITION] 포지션 조회 실패: {e}")
        return {}


def has_position(symbol: str) -> bool:
    """해당 심볼 포지션 보유 여부"""
    positions = get_open_positions()
    return symbol in positions


def get_position_age_hours(symbol: str) -> float:
    """포지션 보유 시간 (시간 단위)"""
    positions = get_open_positions()
    if symbol not in positions:
        return 0.0
    ts = positions[symbol].get("timestamp", 0)
    if not ts:
        return 0.0
    return (time.time() * 1000 - ts) / 3_600_000


# main.py에서 호출하는 함수명 (alias)
get_position_age_bars = get_position_age_hours
