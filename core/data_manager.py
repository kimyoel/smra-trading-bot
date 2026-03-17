"""
core/data_manager.py — ccxt OHLCV fetch + 캐시
같은 심볼+타임프레임은 1루프 내 중복 호출 방지
"""

import os
import time
import ccxt
import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_manager")

# ── 거래소 초기화 ────────────────────────────────────────────
exchange = ccxt.binance({
    "apiKey":  os.getenv("BINANCE_API_KEY", ""),
    "secret":  os.getenv("BINANCE_API_SECRET", ""),
    "options": {"defaultType": "future"},
    "enableRateLimit": True,
})

# ── 1루프 캐시 ───────────────────────────────────────────────
_cache: dict = {}   # key: "SYMBOL_TF", value: (timestamp, DataFrame)
CACHE_TTL_SEC = 55  # 55초 이내 재요청은 캐시 반환


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame | None:
    """
    OHLCV 데이터 fetch. 캐시 히트 시 캐시 반환.
    반환: columns = [timestamp, open, high, low, close, volume]
    """
    key = f"{symbol}_{timeframe}"
    now = time.time()

    if key in _cache:
        ts, df = _cache[key]
        if now - ts < CACHE_TTL_SEC:
            return df

    try:
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            logger.warning(f"[DATA] {key} — 빈 응답")
            return None

        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})

        _cache[key] = (now, df)
        return df

    except ccxt.NetworkError as e:
        logger.error(f"[DATA] 네트워크 오류 {key}: {e}")
        return None
    except ccxt.ExchangeError as e:
        logger.error(f"[DATA] 거래소 오류 {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"[DATA] 알 수 없는 오류 {key}: {e}")
        return None


def fetch_funding_rate(symbol: str) -> float:
    """현재 펀딩비 반환"""
    try:
        info = exchange.fetch_funding_rate(symbol)
        return float(info.get("fundingRate", 0.0))
    except Exception as e:
        logger.warning(f"[DATA] 펀딩비 조회 실패 {symbol}: {e}")
        return 0.0


def fetch_orderbook(symbol: str) -> dict | None:
    """호가창 조회 (스프레드 계산용)"""
    try:
        ob = exchange.fetch_order_book(symbol, limit=5)
        return ob
    except Exception as e:
        logger.warning(f"[DATA] 호가창 조회 실패 {symbol}: {e}")
        return None


def get_balance() -> float:
    """USDT 사용 가능 잔고 반환"""
    try:
        bal = exchange.fetch_balance()
        return float(bal["USDT"]["free"])
    except Exception as e:
        logger.error(f"[DATA] 잔고 조회 실패: {e}")
        return 0.0


def clear_cache() -> None:
    """루프 시작 시 캐시 초기화"""
    _cache.clear()
