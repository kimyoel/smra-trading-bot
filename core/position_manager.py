"""
core/position_manager.py — 심볼당 1포지션 상태 추적 (v2.9)

수정 히스토리:
  v2.8: ccxt unified symbol 정규화 (BTC/USDT:USDT → BTC/USDT)
  v2.9:
  [FIX1] _position_timeframe in-memory → JSON 파일 영속화
         Railway 재시작 후에도 TF 정보 유지 (5m 포지션이 24h 기준 적용되는 버그 방지)
  [FIX2] 포지션 오픈 시간 봇 자체 기록 (entry_time)
         Binance fetch_positions의 timestamp = updateTime (업데이트 시간, 오픈 시간 아님)
         → 봇이 직접 기록한 entry_time 사용으로 age 계산 정확도 확보
  [FIX3] 포지션이 닫히면 state.json에서 자동 정리
"""

import json
import os
import time
import ccxt
from core.data_manager import exchange
from utils.logger import get_logger

logger = get_logger("position_manager")

# 영속화 파일 경로 (Railway 볼륨 또는 로컬)
_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "position_state.json")


def _ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)


def _load_state() -> dict:
    """JSON 파일에서 포지션 상태 로드"""
    _ensure_data_dir()
    if not os.path.exists(_STATE_FILE):
        return {}
    try:
        with open(_STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"[POSITION] state.json 로드 실패 — 초기화: {e}")
        return {}


def _save_state(state: dict) -> None:
    """JSON 파일에 포지션 상태 저장"""
    _ensure_data_dir()
    try:
        with open(_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"[POSITION] state.json 저장 실패: {e}")


def normalize_symbol(symbol: str) -> str:
    """
    ccxt unified symbol 정규화.
    'BTC/USDT:USDT' → 'BTC/USDT'
    """
    if ':' in symbol:
        return symbol.split(':')[0]
    return symbol


def record_position_timeframe(symbol: str, timeframe: str) -> None:
    """
    진입 시 타임프레임 + 진입 시각 기록 (v2.9: 파일 영속화).
    order 성공 직후 main.py에서 호출.
    """
    state = _load_state()
    state[symbol] = {
        "timeframe":  timeframe,
        "entry_time": time.time(),   # Unix timestamp (초)
    }
    _save_state(state)
    logger.info(f"[POSITION] 진입 기록: {symbol} TF={timeframe} at {time.strftime('%H:%M:%S')}")


def _cleanup_closed_positions(open_symbols: set) -> None:
    """
    현재 열린 포지션 목록과 비교해 닫힌 포지션 state.json에서 제거.
    """
    state = _load_state()
    removed = [s for s in list(state.keys()) if s not in open_symbols]
    if removed:
        for s in removed:
            del state[s]
        _save_state(state)
        logger.info(f"[POSITION] 청산 확인 — state.json 정리: {removed}")


def get_open_positions() -> dict:
    """
    현재 열린 포지션 조회.
    반환: {symbol: position_info}
    예: {"BTC/USDT": {"side": "long", "size": 0.001, "entry": 85000.0, "timeframe": "5m", "entry_time": 1234567890.0}}
    """
    try:
        positions = exchange.fetch_positions()
        state     = _load_state()
        result    = {}

        for pos in positions:
            size = float(pos.get("contracts", 0) or 0)
            if size == 0:
                continue
            symbol     = normalize_symbol(pos["symbol"])
            saved      = state.get(symbol, {})
            # 봇이 기록한 entry_time 우선, 없으면 Binance updateTime 폴백
            binance_ts = pos.get("timestamp")  # ms 또는 None
            entry_time = saved.get("entry_time") or (
                (binance_ts / 1000) if binance_ts else time.time()
            )
            result[symbol] = {
                "side":           pos.get("side", "long"),
                "size":           size,
                "entry":          float(pos.get("entryPrice", 0) or 0),
                "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
                "entry_time":     entry_time,
                # TF: 봇 기록 우선, 없으면 "1h" 기본 (재시작 후 미기록 케이스)
                "timeframe":      saved.get("timeframe", "1h"),
                "raw_symbol":     pos["symbol"],
            }

        # 닫힌 포지션 정리
        _cleanup_closed_positions(set(result.keys()))
        return result

    except Exception as e:
        logger.error(f"[POSITION] 포지션 조회 실패: {e}")
        return {}


def has_position(symbol: str) -> bool:
    """해당 심볼 포지션 보유 여부"""
    return symbol in get_open_positions()


def get_position_age_hours(symbol: str) -> float:
    """
    포지션 보유 시간 (시간 단위).
    봇 자체 기록 entry_time 기반 → 정확한 오픈 시간 반영.
    """
    positions = get_open_positions()
    if symbol not in positions:
        return 0.0
    entry_time = positions[symbol].get("entry_time", 0)
    if not entry_time:
        return 0.0
    return (time.time() - entry_time) / 3600.0


# main.py에서 호출하는 함수명 (alias)
get_position_age_bars = get_position_age_hours
