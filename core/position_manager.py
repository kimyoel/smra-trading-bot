"""
core/position_manager.py — 헤지 모드 포지션 상태 추적 (v3.0)

[v3.0] 헤지 모드 전면 전환
  - 포지션 키 변경: symbol → "symbol:LONG" / "symbol:SHORT" 복합 키
  - 동일 심볼에 LONG + SHORT 독립 포지션 최대 1개씩 허용
  - get_open_positions(): Binance fetch_positions()에서 positionSide 별 분리
  - record_position_timeframe(): pos_key = "symbol:direction" 형태로 기록
  - state.json 구조: {"BTC/USDT:LONG": {...}, "BTC/USDT:SHORT": {...}}
  - has_position(symbol, direction): 특정 방향의 포지션 존재 여부
  - get_position_age_hours(pos_key): 복합 키 기반 보유 시간 조회

수정 히스토리:
  v2.11: record_position_timeframe() strategy_id 추가
  v2.10: get_open_positions_live(), get_realtime_position_size(), get_open_algo_orders()
  v2.9 : state.json 영속화, 봇 자체 entry_time 기록
  v2.8 : ccxt unified symbol 정규화
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


def make_pos_key(symbol: str, direction: str) -> str:
    """
    [v3.0] 포지션 복합 키 생성.
    "BTC/USDT" + "long" → "BTC/USDT:LONG"
    """
    return f"{symbol}:{direction.upper()}"


def parse_pos_key(pos_key: str) -> tuple[str, str]:
    """
    [v3.0] 복합 키에서 심볼과 방향 분리.
    "BTC/USDT:LONG" → ("BTC/USDT", "long")
    """
    if ":" in pos_key:
        parts = pos_key.rsplit(":", 1)
        return parts[0], parts[1].lower()
    return pos_key, "long"


def record_position_timeframe(
    symbol: str, timeframe: str, strategy_id: str = "", direction: str = "long"
) -> None:
    """
    진입 시 타임프레임 + 진입 시각 + 전략 ID 기록 (v3.0: direction 추가).
    order 성공 직후 main.py에서 호출.

    [v3.0] 키 변경: symbol → "symbol:DIRECTION"
    state.json 구조:
        {"BTC/USDT:LONG": {"timeframe": "5m", "entry_time": 1234567890.0, "strategy_id": "..."}}
    """
    pos_key = make_pos_key(symbol, direction)
    state = _load_state()
    state[pos_key] = {
        "timeframe":   timeframe,
        "entry_time":  time.time(),
        "strategy_id": strategy_id,
        "direction":   direction.lower(),
    }
    _save_state(state)
    logger.info(
        f"[POSITION] 진입 기록: {pos_key} | TF={timeframe} | 전략={strategy_id or '?'} "
        f"| at {time.strftime('%H:%M:%S')}"
    )


def _cleanup_closed_positions(open_pos_keys: set) -> None:
    """
    현재 열린 포지션 목록과 비교해 닫힌 포지션 state.json에서 제거.
    [v3.0] 키가 "symbol:DIRECTION" 형태.
    """
    state = _load_state()
    removed = [k for k in list(state.keys()) if k not in open_pos_keys]
    if removed:
        for k in removed:
            del state[k]
        _save_state(state)
        logger.info(f"[POSITION] 청산 확인 — state.json 정리: {removed}")


# ── [v2.10] Binance 실시간 단독 조회 함수들 ─────────────────

def get_realtime_position_size(symbol: str, direction: str = "long") -> float:
    """
    [v3.0] Binance fetch_positions()로 실시간 포지션 크기 조회.
    헤지 모드: positionSide 매칭하여 해당 방향 포지션만 반환.
    """
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos.get("contracts", 0) or 0)
            if contracts > 0:
                pos_sym = normalize_symbol(pos["symbol"])
                pos_side = (pos.get("side", "long") or "long").lower()
                if pos_sym == normalize_symbol(symbol) and pos_side == direction:
                    logger.info(
                        f"[POSITION] 실시간 포지션 크기 조회: {symbol} [{direction.upper()}] = {contracts}"
                    )
                    return contracts
        return 0.0
    except Exception as e:
        logger.error(f"[POSITION] 실시간 포지션 크기 조회 실패 {symbol}: {e}")
        return 0.0


def get_open_algo_orders(symbol: str) -> list:
    """
    [v2.10] 해당 심볼의 현재 등록된 Algo Order(TP/SL) 목록 조회.
    반환: [{algoId, orderType, side, stopPrice, positionSide, ...}, ...]
    """
    raw_symbol = symbol.split(":")[0].replace("/", "")
    try:
        resp = exchange.fapiPrivateGetOpenAlgoOrders({"symbol": raw_symbol})
        orders = resp.get("orders", []) if isinstance(resp, dict) else resp
        logger.info(f"[POSITION] {symbol} 열린 Algo Order: {len(orders)}개")
        for o in orders:
            logger.info(
                f"  algoId={o.get('algoId')} | type={o.get('orderType')} | "
                f"positionSide={o.get('positionSide', '?')} | "
                f"stopPrice={o.get('triggerPrice', o.get('stopPrice', '?'))}"
            )
        return orders
    except Exception as e:
        logger.warning(f"[POSITION] Algo Order 조회 실패 {symbol}: {e}")
        return []


def get_open_positions() -> dict:
    """
    현재 열린 포지션 조회 (v3.0: 헤지 모드 — positionSide별 독립 추적).

    [v3.0] 반환 키: "symbol:LONG", "symbol:SHORT" (복합 키)
           동일 심볼에 LONG + SHORT 2개의 독립 포지션 가능

    반환: {pos_key: {side, size, entry, unrealized_pnl, entry_time, timeframe, strategy_id, raw_symbol}}
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
            direction  = (pos.get("side", "long") or "long").lower()
            pos_key    = make_pos_key(symbol, direction)
            saved      = state.get(pos_key, {})

            # entry_time: 봇 기록 우선 → Binance updateTime 폴백 → 현재 시각 폴백
            binance_ts = pos.get("timestamp")
            entry_time = saved.get("entry_time") or (
                (binance_ts / 1000) if binance_ts else time.time()
            )

            result[pos_key] = {
                "side":           direction,
                "size":           size,
                "entry":          float(pos.get("entryPrice", 0) or 0),
                "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),
                "entry_time":     entry_time,
                "timeframe":      saved.get("timeframe", "1h"),
                "strategy_id":    saved.get("strategy_id", ""),
                "raw_symbol":     pos["symbol"],
                "symbol":         symbol,
            }

        # 닫힌 포지션 정리
        _cleanup_closed_positions(set(result.keys()))
        return result

    except Exception as e:
        logger.error(f"[POSITION] 포지션 조회 실패: {e}")
        return {}


def has_position(symbol: str, direction: str = "") -> bool:
    """
    [v3.0] 해당 심볼/방향 포지션 보유 여부.

    direction="" → 해당 심볼의 어느 방향이든 포지션이 있으면 True
    direction="long"/"short" → 특정 방향만 체크
    """
    positions = get_open_positions()
    if direction:
        pos_key = make_pos_key(symbol, direction)
        return pos_key in positions
    else:
        long_key  = make_pos_key(symbol, "long")
        short_key = make_pos_key(symbol, "short")
        return long_key in positions or short_key in positions


def get_position_age_hours(pos_key: str) -> float:
    """
    포지션 보유 시간 (시간 단위).
    [v3.0] pos_key = "symbol:LONG" / "symbol:SHORT"
    """
    positions = get_open_positions()
    if pos_key not in positions:
        return 0.0
    entry_time = positions[pos_key].get("entry_time", 0)
    if not entry_time:
        return 0.0
    return (time.time() - entry_time) / 3600.0


# main.py에서 호출하는 함수명 (alias)
get_position_age_bars = get_position_age_hours
