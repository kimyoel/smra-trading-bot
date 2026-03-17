"""
core/position_manager.py — 심볼당 1포지션 상태 추적 (v2.11)

수정 히스토리:
  v2.8 : ccxt unified symbol 정규화 (BTC/USDT:USDT → BTC/USDT)
  v2.9 : _position_timeframe in-memory → JSON 파일 영속화,
          봇 자체 entry_time 기록 (Binance updateTime 대신),
          포지션 닫히면 state.json 자동 정리
  v2.10:
  [FIX1] get_open_positions_live(): Binance fetch_positions() 직접 조회 함수 분리
  [FIX2] get_realtime_position_size(): 강제청산/조회 시 Binance 실시간 크기 단독 조회
  [FIX3] get_open_algo_orders(): 현재 등록된 Algo Order(TP/SL) 목록 조회
  v2.11:
  [FIX4] record_position_timeframe(): strategy_id 파라미터 추가 → state.json에 저장
         → 24봉 강제청산 로그, 포지션 추적 시 어떤 전략으로 진입했는지 기록
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


def record_position_timeframe(symbol: str, timeframe: str, strategy_id: str = "") -> None:
    """
    진입 시 타임프레임 + 진입 시각 + 전략 ID 기록 (v2.11: strategy_id 추가).
    order 성공 직후 main.py에서 호출.

    state.json 구조:
        {"BTC/USDT": {"timeframe": "5m", "entry_time": 1234567890.0, "strategy_id": "BTC_5m_PSAR_ROC"}}
    """
    state = _load_state()
    state[symbol] = {
        "timeframe":   timeframe,
        "entry_time":  time.time(),   # Unix timestamp (초)
        "strategy_id": strategy_id,   # v2.11: 어떤 전략으로 진입했는지 기록
    }
    _save_state(state)
    logger.info(
        f"[POSITION] 진입 기록: {symbol} | TF={timeframe} | 전략={strategy_id or '?'} "
        f"| at {time.strftime('%H:%M:%S')}"
    )


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


# ── [v2.10] Binance 실시간 단독 조회 함수들 ─────────────────

def get_realtime_position_size(symbol: str) -> float:
    """
    [v2.10] Binance fetch_positions()로 실시간 포지션 크기만 단독 조회.

    강제청산 등 size가 중요한 순간에 사용.
    조회 실패 시 0.0 반환 (호출부에서 폴백 처리).
    """
    try:
        positions = exchange.fetch_positions([symbol])
        for pos in positions:
            contracts = float(pos.get("contracts", 0) or 0)
            if contracts > 0:
                pos_sym = normalize_symbol(pos["symbol"])
                if pos_sym == normalize_symbol(symbol):
                    logger.info(
                        f"[POSITION] 실시간 포지션 크기 조회: {symbol} = {contracts}"
                    )
                    return contracts
        return 0.0
    except Exception as e:
        logger.error(f"[POSITION] 실시간 포지션 크기 조회 실패 {symbol}: {e}")
        return 0.0


def get_open_algo_orders(symbol: str) -> list:
    """
    [v2.10] 해당 심볼의 현재 등록된 Algo Order(TP/SL) 목록 조회.

    Binance /fapi/v1/openAlgoOrders 직접 조회.
    TP/SL이 정상 등록되어 있는지 확인할 때 사용.
    반환: [{algoId, orderType, side, stopPrice, ...}, ...]
    """
    raw_symbol = symbol.split(":")[0].replace("/", "")
    try:
        resp = exchange.fapiPrivateGetOpenAlgoOrders({"symbol": raw_symbol})
        orders = resp.get("orders", []) if isinstance(resp, dict) else resp
        logger.info(f"[POSITION] {symbol} 열린 Algo Order: {len(orders)}개")
        for o in orders:
            logger.info(
                f"  algoId={o.get('algoId')} | type={o.get('orderType')} | "
                f"stopPrice={o.get('triggerPrice', o.get('stopPrice', '?'))}"
            )
        return orders
    except Exception as e:
        logger.warning(f"[POSITION] Algo Order 조회 실패 {symbol}: {e}")
        return []


def get_open_positions() -> dict:
    """
    현재 열린 포지션 조회 (v2.10: Binance 실시간 우선).

    데이터 계층:
      - 포지션 크기/진입가/PnL → Binance fetch_positions() 실시간 데이터
      - entry_time/timeframe   → state.json (Binance가 진입 시각 미제공이므로 로컬 유지)

    반환: {symbol: {side, size, entry, unrealized_pnl, entry_time, timeframe, raw_symbol}}
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

            # entry_time: 봇 기록 우선 → Binance updateTime 폴백 → 현재 시각 폴백
            binance_ts = pos.get("timestamp")   # ms
            entry_time = saved.get("entry_time") or (
                (binance_ts / 1000) if binance_ts else time.time()
            )

            result[symbol] = {
                "side":           pos.get("side", "long"),
                "size":           size,                                  # ← Binance 실시간
                "entry":          float(pos.get("entryPrice", 0) or 0),  # ← Binance 실시간
                "unrealized_pnl": float(pos.get("unrealizedPnl", 0) or 0),  # ← Binance 실시간
                "entry_time":     entry_time,                            # ← state.json 우선
                "timeframe":      saved.get("timeframe", "1h"),          # ← state.json 우선
                "strategy_id":    saved.get("strategy_id", ""),          # ← v2.11: 전략 ID
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
